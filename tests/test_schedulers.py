
"""
Test suite for traffic intersection scheduling algorithms
"""

import pytest
from typing import Dict, List
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'flask_app'))

from schedulers import (
    TrafficScheduler, IntersectionState, EmergencyVehicle, 
    SchedulingPolicy, Phase, ActionPlan, simulate_one_step
)


class TestTrafficScheduler:
    """Test cases for traffic scheduling algorithms"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.scheduler = TrafficScheduler()
        self.basic_state = IntersectionState(
            queues={'N': 3, 'E': 2, 'S': 1, 'W': 4},
            waiting_times={
                'N': [10.0, 15.0, 20.0],
                'E': [5.0, 8.0],
                'S': [12.0],
                'W': [25.0, 30.0, 18.0, 22.0]
            },
            arrival_rates={'N': 0.1, 'E': 0.05, 'S': 0.08, 'W': 0.12},
            emergency=[],
            current_phase='NS_green',
            sim_time=100.0
        )
    
    def test_rr_basic(self):
        """Test Round Robin scheduling cycles through phases in order"""
        state = self.basic_state
        
        # Test cycling from NS_green to EW_green
        plan = self.scheduler.schedule(state, SchedulingPolicy.ROUND_ROBIN)
        
        # Should have transition phases (yellow, all_red) and next green phase
        assert len(plan) >= 1
        
        # Find the green phase in the plan
        green_phases = [p for p in plan if 'green' in p.phase and 'yellow' not in p.phase]
        assert len(green_phases) == 1
        
        green_phase = green_phases[0]
        assert green_phase.phase == 'EW_green'  # Next in RR cycle
        
        # Duration should be within limits
        assert self.scheduler.policy_params['min_green'] <= green_phase.duration <= self.scheduler.policy_params['max_green']
    
    def test_sjf_reduces_avg_wait(self):
        """Test SJF selects phase with smallest job count"""
        # Create state where one direction has fewer vehicles
        state = IntersectionState(
            queues={'N': 1, 'E': 5, 'S': 1, 'W': 5},  # NS has fewer vehicles
            waiting_times={
                'N': [5.0],
                'E': [10.0, 15.0, 20.0, 25.0, 30.0],
                'S': [8.0],
                'W': [12.0, 18.0, 22.0, 28.0, 35.0]
            },
            arrival_rates={'N': 0.02, 'E': 0.08, 'S': 0.02, 'W': 0.08},
            emergency=[],
            current_phase='EW_green',
            sim_time=50.0
        )
        
        # SJF should select NS_green (fewer vehicles)
        plan = self.scheduler.schedule(state, SchedulingPolicy.SHORTEST_JOB_FIRST)
        
        green_phases = [p for p in plan if 'green' in p.phase and 'yellow' not in p.phase]
        assert len(green_phases) == 1
        assert green_phases[0].phase == 'NS_green'  # Should select the direction with fewer vehicles
    
    def test_emergency_preempt(self):
        """Test emergency vehicle forces immediate preemption"""
        emergency_state = IntersectionState(
            queues={'N': 2, 'E': 3, 'S': 1, 'W': 2},
            waiting_times={'N': [5.0, 8.0], 'E': [10.0, 12.0, 15.0], 'S': [7.0], 'W': [9.0, 11.0]},
            arrival_rates={'N': 0.05, 'E': 0.07, 'S': 0.03, 'W': 0.06},
            emergency=[EmergencyVehicle(direction='N', time_to_intersection=4.0, vehicle_id='EMG001')],
            current_phase='EW_green',
            sim_time=200.0
        )
        
        plan = self.scheduler.schedule(emergency_state, SchedulingPolicy.META)
        
        # Should immediately switch to emergency direction
        assert len(plan) >= 1
        
        # Find the final green phase
        green_phases = [p for p in plan if 'green' in p.phase and 'yellow' not in p.phase]
        assert len(green_phases) == 1
        assert green_phases[0].phase == 'NS_green'  # Emergency vehicle direction
        assert not green_phases[0].preemptable  # Emergency phases should not be preemptable
    
    def test_meta_switch(self):
        """Test meta-scheduler selects appropriate policy based on conditions"""
        scheduler = TrafficScheduler({'debug': True, **self.scheduler.policy_params})
        
        # Test high variance scenario -> should select SJF
        high_variance_state = IntersectionState(
            queues={'N': 10, 'E': 1, 'S': 8, 'W': 1},  # High variance
            waiting_times={'N': [20.0] * 10, 'E': [5.0], 'S': [15.0] * 8, 'W': [3.0]},
            arrival_rates={'N': 0.1, 'E': 0.01, 'S': 0.08, 'W': 0.01},
            emergency=[],
            current_phase='EW_green',
            sim_time=300.0
        )
        
        # Meta-scheduler should select SJF for high variance
        selected_policy = scheduler._select_policy(high_variance_state)
        assert selected_policy == SchedulingPolicy.SHORTEST_JOB_FIRST
        
        # Test low load scenario -> should select RR
        low_load_state = IntersectionState(
            queues={'N': 1, 'E': 1, 'S': 1, 'W': 1},  # Low, uniform load
            waiting_times={'N': [5.0], 'E': [5.0], 'S': [5.0], 'W': [5.0]},
            arrival_rates={'N': 0.02, 'E': 0.02, 'S': 0.02, 'W': 0.02},
            emergency=[],
            current_phase='NS_green',
            sim_time=400.0
        )
        
        selected_policy = scheduler._select_policy(low_load_state)
        assert selected_policy == SchedulingPolicy.ROUND_ROBIN
    
    def test_empty_queues_handling(self):
        """Test handling of empty queues"""
        empty_state = IntersectionState(
            queues={'N': 0, 'E': 0, 'S': 0, 'W': 0},
            waiting_times={'N': [], 'E': [], 'S': [], 'W': []},
            arrival_rates={'N': 0.01, 'E': 0.01, 'S': 0.01, 'W': 0.01},
            emergency=[],
            current_phase='all_red',
            sim_time=500.0
        )
        
        plan = self.scheduler.schedule(empty_state, SchedulingPolicy.ROUND_ROBIN)
        
        # Should still produce a valid plan
        assert len(plan) >= 1
        
        # Duration should respect minimum green time
        green_phases = [p for p in plan if 'green' in p.phase]
        if green_phases:
            assert green_phases[0].duration >= self.scheduler.policy_params['min_green']
    
    def test_multiple_emergency_vehicles(self):
        """Test handling of multiple emergency vehicles"""
        multi_emergency_state = IntersectionState(
            queues={'N': 2, 'E': 1, 'S': 3, 'W': 2},
            waiting_times={'N': [10.0, 12.0], 'E': [8.0], 'S': [15.0, 18.0, 20.0], 'W': [9.0, 11.0]},
            arrival_rates={'N': 0.05, 'E': 0.03, 'S': 0.07, 'W': 0.05},
            emergency=[
                EmergencyVehicle(direction='E', time_to_intersection=8.0, vehicle_id='EMG001'),
                EmergencyVehicle(direction='N', time_to_intersection=5.0, vehicle_id='EMG002')
            ],
            current_phase='EW_green',
            sim_time=600.0
        )
        
        plan = self.scheduler.schedule(multi_emergency_state, SchedulingPolicy.META)
        
        # Should prioritize the emergency vehicle with smaller ETA (North, 5.0s)
        green_phases = [p for p in plan if 'green' in p.phase and 'yellow' not in p.phase]
        assert len(green_phases) == 1
        assert green_phases[0].phase == 'NS_green'
    
    def test_phase_duration_constraints(self):
        """Test that phase durations respect min/max constraints"""
        # Test with very high vehicle count
        high_count_state = IntersectionState(
            queues={'N': 50, 'E': 2, 'S': 45, 'W': 2},
            waiting_times={'N': [30.0] * 50, 'E': [5.0, 6.0], 'S': [25.0] * 45, 'W': [4.0, 5.0]},
            arrival_rates={'N': 0.2, 'E': 0.02, 'S': 0.18, 'W': 0.02},
            emergency=[],
            current_phase='EW_green',
            sim_time=700.0
        )
        
        plan = self.scheduler.schedule(high_count_state, SchedulingPolicy.PRIORITY)
        
        green_phases = [p for p in plan if 'green' in p.phase and 'yellow' not in p.phase]
        if green_phases:
            duration = green_phases[0].duration
            assert self.scheduler.policy_params['min_green'] <= duration <= self.scheduler.policy_params['max_green']
    
    def test_explain_decision(self):
        """Test decision explanation functionality"""
        scheduler = TrafficScheduler()
        
        # Test emergency explanation
        explanation = scheduler.explain_decision(
            IntersectionState(
                queues={'N': 1, 'E': 1, 'S': 1, 'W': 1},
                waiting_times={'N': [5.0], 'E': [5.0], 'S': [5.0], 'W': [5.0]},
                arrival_rates={'N': 0.02, 'E': 0.02, 'S': 0.02, 'W': 0.02},
                emergency=[EmergencyVehicle('N', 3.0, 'EMG001')],
                current_phase='NS_green',
                sim_time=100.0
            ),
            SchedulingPolicy.PRIORITY
        )
        
        assert "Emergency" in explanation
        assert "Priority" in explanation
    
    def test_safety_transitions(self):
        """Test that transitions include proper yellow and all-red phases"""
        state = IntersectionState(
            queues={'N': 2, 'E': 3, 'S': 1, 'W': 2},
            waiting_times={'N': [10.0, 12.0], 'E': [8.0, 10.0, 12.0], 'S': [9.0], 'W': [11.0, 13.0]},
            arrival_rates={'N': 0.05, 'E': 0.06, 'S': 0.03, 'W': 0.05},
            emergency=[],
            current_phase='NS_green',
            sim_time=800.0
        )
        
        plan = self.scheduler.schedule(state, SchedulingPolicy.ROUND_ROBIN)
        
        # Should have yellow and all_red phases before green
        phase_names = [p.phase for p in plan]
        
        if len(phase_names) > 1:
            # Should have safety phases
            assert any('yellow' in phase or 'all_red' in phase for phase in phase_names)


def test_simulate_one_step():
    """Test simulation helper function"""
    initial_state = IntersectionState(
        queues={'N': 2, 'E': 1, 'S': 1, 'W': 3},
        waiting_times={'N': [10.0, 12.0], 'E': [8.0], 'S': [9.0], 'W': [15.0, 18.0, 20.0]},
        arrival_rates={'N': 0.05, 'E': 0.03, 'S': 0.03, 'W': 0.07},
        emergency=[],
        current_phase='all_red',
        sim_time=1000.0
    )
    
    action_plan = [Phase('NS_green', 15.0, True)]
    
    new_state = simulate_one_step(initial_state, action_plan)
    
    assert new_state.current_phase == 'NS_green'
    assert new_state.sim_time == 1015.0
    assert new_state.queues == initial_state.queues  # Queues unchanged in simple simulation


if __name__ == '__main__':
    pytest.main([__file__])
