
"""
Smart Traffic Intersection Scheduling Layer

This module implements various scheduling algorithms for traffic intersection management,
including Round Robin, Shortest Job First, Priority Scheduling, and a Meta-Scheduler
that dynamically selects the best algorithm based on traffic conditions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import math
import logging
from enum import Enum


@dataclass
class EmergencyVehicle:
    """Emergency vehicle information"""
    direction: str  # "N", "E", "S", "W"
    time_to_intersection: float  # ETA in seconds
    vehicle_id: str
    priority: int = 1  # Lower number = higher priority


@dataclass
class IntersectionState:
    """Current state of the traffic intersection"""
    queues: Dict[str, int]  # Vehicle counts per direction: "N","E","S","W"
    waiting_times: Dict[str, List[float]]  # Per-vehicle waiting times (seconds)
    arrival_rates: Dict[str, float]  # Estimated arrival rate (vehicles/sec)
    emergency: List[EmergencyVehicle]  # Emergency vehicles
    current_phase: str  # e.g., "NS_green", "EW_green", "all_red"
    sim_time: float  # Current simulation time in seconds


@dataclass
class Phase:
    """Traffic light phase definition"""
    phase: str  # Phase name (e.g., "NS_green", "EW_green", "all_red")
    duration: float  # Duration in seconds
    preemptable: bool = True  # Can be interrupted by emergency vehicles


ActionPlan = List[Phase]


class SchedulingPolicy(Enum):
    """Available scheduling policies"""
    ROUND_ROBIN = "RR"
    SHORTEST_JOB_FIRST = "SJF"
    PRIORITY = "PRIORITY"
    META = "META"


class TrafficScheduler:
    """Main traffic scheduling class implementing multiple algorithms"""
    
    def __init__(self, policy_params: Optional[Dict[str, Any]] = None):
        """
        Initialize the traffic scheduler
        
        Args:
            policy_params: Configuration parameters for scheduling policies
        """
        self.policy_params = policy_params or self._get_default_params()
        self.logger = logging.getLogger(__name__)
        
        # State tracking for meta-scheduler
        self._last_phase_switch_time = {}
        self._policy_history = []
    
    def _get_default_params(self) -> Dict[str, Any]:
        """Get default policy parameters"""
        return {
            'min_green': 7.0,
            'max_green': 60.0,
            'yellow_duration': 3.0,
            'all_red_duration': 1.0,
            'rr_cycle_order': ['NS_green', 'EW_green'],
            'low_load_threshold': 2.0,
            'high_variance_threshold': 4.0,
            'sjf_horizon': 30.0,
            'emergency_preempt_buffer': 10.0,
            'min_switch_interval': 5.0,
            'emergency_clear_duration': 15.0,
            'debug': False
        }
    
    def schedule(self, state: IntersectionState, policy: SchedulingPolicy = SchedulingPolicy.META) -> ActionPlan:
        """
        Generate action plan for the given intersection state
        
        Args:
            state: Current intersection state
            policy: Scheduling policy to use
            
        Returns:
            ActionPlan with scheduled phases
        """
        if self.policy_params['debug']:
            self.logger.info(f"Scheduling with policy: {policy.value}")
        
        # Check for emergency vehicles first
        if self._has_urgent_emergency(state):
            return self._handle_emergency(state)
        
        # Select policy (meta-scheduler logic)
        if policy == SchedulingPolicy.META:
            policy = self._select_policy(state)
            if self.policy_params['debug']:
                reason = self.explain_decision(state, policy)
                self.logger.info(f"Meta-scheduler selected {policy.value}: {reason}")
        
        # Generate plan based on selected policy
        if policy == SchedulingPolicy.ROUND_ROBIN:
            return self._round_robin_schedule(state)
        elif policy == SchedulingPolicy.SHORTEST_JOB_FIRST:
            return self._sjf_schedule(state)
        elif policy == SchedulingPolicy.PRIORITY:
            return self._priority_schedule(state)
        else:
            raise ValueError(f"Unsupported policy: {policy}")
    
    def _has_urgent_emergency(self, state: IntersectionState) -> bool:
        """Check if there are urgent emergency vehicles requiring immediate attention"""
        emergency_buffer = self.policy_params['emergency_preempt_buffer']
        
        for ev in state.emergency:
            if ev.time_to_intersection <= emergency_buffer:
                return True
            # Also check if emergency vehicle is already in queue
            if state.queues.get(ev.direction, 0) > 0:
                return True
        return False
    
    def _handle_emergency(self, state: IntersectionState) -> ActionPlan:
        """Generate emergency preemption plan using FCFS for multiple emergencies"""
        # Group emergency vehicles by direction to avoid conflicts
        emergency_by_direction = {}
        for ev in state.emergency:
            if ev.direction not in emergency_by_direction:
                emergency_by_direction[ev.direction] = []
            emergency_by_direction[ev.direction].append(ev)
        
        # If multiple directions have emergency vehicles, use FCFS based on arrival time
        if len(emergency_by_direction) > 1:
            # Find the emergency vehicle that will arrive first (FCFS)
            earliest_ev = min(state.emergency, key=lambda ev: ev.time_to_intersection)
            target_direction = earliest_ev.direction
            
            if self.policy_params['debug']:
                self.logger.info(f"Multiple emergencies detected. Using FCFS: {target_direction} arrives in {earliest_ev.time_to_intersection}s")
        else:
            # Single direction emergency - use priority-based selection
            urgent_ev = min(state.emergency, 
                           key=lambda ev: (ev.time_to_intersection, ev.priority))
            target_direction = urgent_ev.direction
        
        target_phase = self._get_green_phase_for_direction(target_direction)
        plan = []
        
        # If we need to switch phases, add transition phases
        if state.current_phase != target_phase and state.current_phase != 'all_red':
            plan.extend(self._schedule_transition_with_yellow(state.current_phase, target_phase))
        
        # Calculate duration based on number of emergency vehicles in this direction
        emergency_count = len(emergency_by_direction.get(target_direction, []))
        base_duration = self.policy_params['emergency_clear_duration']
        emergency_duration = min(base_duration + (emergency_count - 1) * 5, 
                               self.policy_params['max_green'])
        
        plan.append(Phase(target_phase, emergency_duration, preemptable=False))
        
        if self.policy_params['debug']:
            self.logger.info(f"Emergency preemption: {target_direction} for {emergency_duration}s ({emergency_count} vehicles)")
        
        return plan
    
    def _select_policy(self, state: IntersectionState) -> SchedulingPolicy:
        """Meta-scheduler: select appropriate policy based on traffic conditions"""
        # Emergency vehicles always use priority scheduling
        if state.emergency:
            return SchedulingPolicy.PRIORITY
        
        # Calculate traffic metrics
        avg_queue = self._compute_average_queue_length(state)
        queue_variance = self._compute_queue_variance(state)
        
        # Low load -> use simple Round Robin
        if avg_queue < self.policy_params['low_load_threshold']:
            return SchedulingPolicy.ROUND_ROBIN
        
        # High variance -> use SJF to reduce backlog
        if queue_variance > self.policy_params['high_variance_threshold']:
            return SchedulingPolicy.SHORTEST_JOB_FIRST
        
        # Default to priority scheduling for balanced conditions
        return SchedulingPolicy.PRIORITY
    
    def _round_robin_schedule(self, state: IntersectionState) -> ActionPlan:
        """Round Robin scheduling algorithm"""
        plan = []
        cycle_order = self.policy_params['rr_cycle_order']
        
        # Find next phase in cycle
        try:
            current_index = cycle_order.index(state.current_phase)
            next_index = (current_index + 1) % len(cycle_order)
        except ValueError:
            next_index = 0
        
        next_phase = cycle_order[next_index]
        
        # Add transition if needed
        if state.current_phase != next_phase and state.current_phase != 'all_red':
            plan.extend(self._schedule_transition_with_yellow(state.current_phase, next_phase))
        
        # Calculate duration based on queue length (proportional)
        direction_queues = self._get_queues_for_phase(state, next_phase)
        total_vehicles = sum(direction_queues.values())
        
        duration = max(self.policy_params['min_green'],
                      min(self.policy_params['max_green'],
                          self.policy_params['min_green'] + total_vehicles * 2))
        
        plan.append(Phase(next_phase, duration, preemptable=True))
        return plan
    
    def _sjf_schedule(self, state: IntersectionState) -> ActionPlan:
        """Shortest Job First scheduling algorithm"""
        plan = []
        
        # Estimate jobs (vehicles + expected arrivals) for each phase
        phase_jobs = {}
        horizon = self.policy_params['sjf_horizon']
        
        for phase in self.policy_params['rr_cycle_order']:
            current_vehicles = sum(self._get_queues_for_phase(state, phase).values())
            expected_arrivals = self._estimate_jobs_in_horizon(state, phase, horizon)
            phase_jobs[phase] = current_vehicles + expected_arrivals
        
        # Select phase with minimum job count
        if phase_jobs:
            next_phase = min(phase_jobs, key=phase_jobs.get)
            
            # Add transition if needed
            if state.current_phase != next_phase and state.current_phase != 'all_red':
                plan.extend(self._schedule_transition_with_yellow(state.current_phase, next_phase))
            
            # Duration based on job count
            job_count = phase_jobs[next_phase]
            duration = max(self.policy_params['min_green'],
                          min(self.policy_params['max_green'],
                              job_count * 3))  # 3 seconds per job
            
            plan.append(Phase(next_phase, duration, preemptable=True))
        
        return plan
    
    def _priority_schedule(self, state: IntersectionState) -> ActionPlan:
        """Priority-based scheduling algorithm"""
        plan = []
        
        # Calculate priority scores for each direction
        direction_priorities = {}
        for direction in ['N', 'E', 'S', 'W']:
            priority = self._calculate_direction_priority(state, direction)
            direction_priorities[direction] = priority
        
        # Find direction with highest priority
        if direction_priorities:
            best_direction = max(direction_priorities, key=direction_priorities.get)
            next_phase = self._get_green_phase_for_direction(best_direction)
            
            # Add transition if needed
            if state.current_phase != next_phase and state.current_phase != 'all_red':
                plan.extend(self._schedule_transition_with_yellow(state.current_phase, next_phase))
            
            # Duration based on priority and queue length
            queue_length = state.queues.get(best_direction, 0)
            base_duration = max(self.policy_params['min_green'], queue_length * 2.5)
            duration = min(self.policy_params['max_green'], base_duration)
            
            plan.append(Phase(next_phase, duration, preemptable=True))
        
        return plan
    
    def _calculate_direction_priority(self, state: IntersectionState, direction: str) -> float:
        """Calculate priority score for a direction"""
        queue_length = state.queues.get(direction, 0)
        waiting_times = state.waiting_times.get(direction, [])
        
        # Base priority from queue length
        priority = queue_length * 2
        
        # Add waiting time component
        if waiting_times:
            avg_wait = sum(waiting_times) / len(waiting_times)
            priority += avg_wait / 10  # Scale down waiting time contribution
        
        # Emergency vehicle bonus
        for ev in state.emergency:
            if ev.direction == direction:
                priority += 100 / ev.priority  # Higher priority = lower number
        
        return priority
    
    def _schedule_transition_with_yellow(self, current_phase: str, target_phase: str) -> List[Phase]:
        """Schedule safe transition between phases with yellow and all-red"""
        transitions = []
        
        if current_phase != 'all_red':
            # Add yellow phase for current direction
            yellow_phase = current_phase.replace('green', 'yellow')
            transitions.append(Phase(yellow_phase, self.policy_params['yellow_duration'], 
                                   preemptable=False))
        
        # Add all-red phase for safety
        transitions.append(Phase('all_red', self.policy_params['all_red_duration'], 
                                preemptable=False))
        
        return transitions
    
    def _get_green_phase_for_direction(self, direction: str) -> str:
        """Get the green phase name for a given direction"""
        if direction in ['N', 'S']:
            return 'NS_green'
        elif direction in ['E', 'W']:
            return 'EW_green'
        else:
            raise ValueError(f"Unknown direction: {direction}")
    
    def _get_queues_for_phase(self, state: IntersectionState, phase: str) -> Dict[str, int]:
        """Get queue counts for directions served by a phase"""
        if phase == 'NS_green':
            return {d: state.queues.get(d, 0) for d in ['N', 'S']}
        elif phase == 'EW_green':
            return {d: state.queues.get(d, 0) for d in ['E', 'W']}
        else:
            return {}
    
    def _compute_average_queue_length(self, state: IntersectionState) -> float:
        """Compute average queue length across all directions"""
        queues = list(state.queues.values())
        return sum(queues) / len(queues) if queues else 0.0
    
    def _compute_queue_variance(self, state: IntersectionState) -> float:
        """Compute variance in queue lengths"""
        queues = list(state.queues.values())
        if len(queues) < 2:
            return 0.0
        
        mean = sum(queues) / len(queues)
        variance = sum((q - mean) ** 2 for q in queues) / len(queues)
        return variance
    
    def _estimate_jobs_in_horizon(self, state: IntersectionState, phase: str, horizon: float) -> float:
        """Estimate number of vehicles arriving within time horizon"""
        directions = []
        if phase == 'NS_green':
            directions = ['N', 'S']
        elif phase == 'EW_green':
            directions = ['E', 'W']
        
        total_arrivals = 0.0
        for direction in directions:
            arrival_rate = state.arrival_rates.get(direction, 0.0)
            total_arrivals += arrival_rate * horizon
        
        return total_arrivals
    
    def explain_decision(self, state: IntersectionState, policy: SchedulingPolicy) -> str:
        """Explain why a particular policy was selected"""
        if state.emergency:
            return "Emergency vehicles present - using Priority scheduling"
        
        avg_queue = self._compute_average_queue_length(state)
        queue_variance = self._compute_queue_variance(state)
        
        if avg_queue < self.policy_params['low_load_threshold']:
            return f"Low traffic load (avg={avg_queue:.1f}) - using Round Robin"
        elif queue_variance > self.policy_params['high_variance_threshold']:
            return f"High queue variance ({queue_variance:.1f}) - using SJF to reduce backlog"
        else:
            return f"Balanced conditions (avg={avg_queue:.1f}, var={queue_variance:.1f}) - using Priority"


# Integration helper functions
def apply_action_plan(sim: Any, action_plan: ActionPlan) -> None:
    """
    Apply action plan to simulation (integration stub)
    
    Args:
        sim: Simulation object with set_phase method
        action_plan: List of phases to execute
    """
    for phase in action_plan:
        sim.set_phase(phase.phase, phase.duration)


def simulate_one_step(state: IntersectionState, action_plan: ActionPlan) -> IntersectionState:
    """
    Simulate one step for testing purposes
    
    Args:
        state: Current intersection state
        action_plan: Action plan to execute
        
    Returns:
        Updated intersection state
    """
    if not action_plan:
        return state
    
    next_phase = action_plan[0]
    new_state = IntersectionState(
        queues=state.queues.copy(),
        waiting_times={k: v.copy() for k, v in state.waiting_times.items()},
        arrival_rates=state.arrival_rates.copy(),
        emergency=state.emergency.copy(),
        current_phase=next_phase.phase,
        sim_time=state.sim_time + next_phase.duration
    )
    
    return new_state
