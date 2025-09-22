"""
Reinforcement Learning Agent for Traffic Light Control
This module implements an RL agent that can learn optimal traffic light timing
"""

import numpy as np
import random
from typing import Dict, List, Tuple
from enum import Enum

class ActionType(Enum):
    EXTEND_GREEN = 0
    SWITCH_TO_YELLOW = 1
    EMERGENCY_OVERRIDE = 2

class TrafficRLAgent:
    def __init__(self, learning_rate=0.1, discount_factor=0.95, epsilon=0.1):
        """
        Initialize the RL agent for traffic control
        
        Args:
            learning_rate: Learning rate for Q-learning
            discount_factor: Discount factor for future rewards
            epsilon: Exploration rate for epsilon-greedy policy
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        
        # Q-table: state -> action -> value
        self.q_table = {}
        
        # State representation: (vehicles_north, vehicles_east, vehicles_south, vehicles_west, current_green_direction, emergency_present)
        self.state_size = 6
        self.action_size = len(ActionType)
        
        # Metrics
        self.total_reward = 0
        self.episode_count = 0
        
    def get_state(self, vehicle_counts: Dict, current_green_direction: int, emergency_present: bool) -> Tuple:
        """
        Convert environment state to a tuple for Q-table indexing
        
        Args:
            vehicle_counts: Dictionary with vehicle counts per direction
            current_green_direction: Current direction with green light (0-3)
            emergency_present: Boolean indicating if emergency vehicle is present
            
        Returns:
            State tuple for Q-table lookup
        """
        # Discretize vehicle counts into bins
        def discretize_count(count):
            if count == 0:
                return 0
            elif count <= 3:
                return 1
            elif count <= 6:
                return 2
            else:
                return 3
        
        state = (
            discretize_count(vehicle_counts.get('north', 0)),
            discretize_count(vehicle_counts.get('east', 0)),
            discretize_count(vehicle_counts.get('south', 0)),
            discretize_count(vehicle_counts.get('west', 0)),
            current_green_direction,
            int(emergency_present)
        )
        
        return state
    
    def get_action(self, state: Tuple) -> ActionType:
        """
        Select action using epsilon-greedy policy
        
        Args:
            state: Current state tuple
            
        Returns:
            Selected action
        """
        if state not in self.q_table:
            self.q_table[state] = np.zeros(self.action_size)
        
        # Epsilon-greedy action selection
        if random.random() < self.epsilon:
            return ActionType(random.randint(0, self.action_size - 1))
        else:
            action_values = self.q_table[state]
            return ActionType(np.argmax(action_values))
    
    def calculate_reward(self, vehicle_counts: Dict, waiting_times: Dict, emergency_served: bool) -> float:
        """
        Calculate reward based on traffic efficiency metrics
        
        Args:
            vehicle_counts: Current vehicle counts per direction
            waiting_times: Average waiting times per direction
            emergency_served: Whether emergency vehicle was served promptly
            
        Returns:
            Calculated reward
        """
        # Base reward components
        total_vehicles = sum(vehicle_counts.values())
        avg_waiting_time = float(np.mean(list(waiting_times.values()))) if waiting_times else 0.0
        
        # Reward calculation
        reward = 0
        
        # Negative reward for high total vehicles (encourages flow)
        reward -= total_vehicles * 0.1
        
        # Negative reward for high waiting times
        reward -= avg_waiting_time * 0.05
        
        # High positive reward for serving emergency vehicles
        if emergency_served:
            reward += 10
        
        # Bonus for balanced traffic (penalize if one direction has too many cars)
        if total_vehicles > 0:
            max_count = max(vehicle_counts.values())
            if max_count > total_vehicles * 0.6:  # More than 60% in one direction
                reward -= 2
        
        return reward
    
    def update_q_table(self, state: Tuple, action: ActionType, reward: float, next_state: Tuple):
        """
        Update Q-table using Q-learning update rule
        
        Args:
            state: Previous state
            action: Action taken
            reward: Reward received
            next_state: Resulting state
        """
        if state not in self.q_table:
            self.q_table[state] = np.zeros(self.action_size)
        if next_state not in self.q_table:
            self.q_table[next_state] = np.zeros(self.action_size)
        
        # Q-learning update
        current_q = self.q_table[state][action.value]
        max_next_q = np.max(self.q_table[next_state])
        
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state][action.value] = new_q
        self.total_reward += reward
    
    def decay_epsilon(self, decay_rate=0.995):
        """Decay exploration rate over time"""
        self.epsilon = max(0.01, self.epsilon * decay_rate)
    
    def get_optimal_timing(self, vehicle_counts: Dict, current_direction: int) -> int:
        """
        Get optimal green light duration based on learned policy
        
        Args:
            vehicle_counts: Current vehicle counts
            current_direction: Current green direction
            
        Returns:
            Optimal green duration in milliseconds
        """
        state = self.get_state(vehicle_counts, current_direction, False)
        
        if state not in self.q_table:
            # Default timing if no learned experience
            return max(3000, min(8000, vehicle_counts.get(f'direction_{current_direction}', 0) * 1000))
        
        # Use learned Q-values to determine timing
        q_values = self.q_table[state]
        
        # If extending green has high value, increase duration
        if q_values[ActionType.EXTEND_GREEN.value] > q_values[ActionType.SWITCH_TO_YELLOW.value]:
            base_duration = 5000
            vehicle_count = sum(vehicle_counts.values())
            return min(10000, base_duration + vehicle_count * 500)
        else:
            return 3000  # Minimum green duration
    
    def save_model(self, filepath: str):
        """Save the Q-table to a file"""
        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump({
                'q_table': self.q_table,
                'total_reward': self.total_reward,
                'episode_count': self.episode_count,
                'epsilon': self.epsilon
            }, f)
    
    def load_model(self, filepath: str):
        """Load the Q-table from a file"""
        import pickle
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                self.q_table = data['q_table']
                self.total_reward = data['total_reward']
                self.episode_count = data['episode_count']
                self.epsilon = data['epsilon']
            return True
        except FileNotFoundError:
            print(f"Model file {filepath} not found. Starting with fresh Q-table.")
            return False
    
    def get_statistics(self) -> Dict:
        """Get learning statistics"""
        return {
            'total_reward': self.total_reward,
            'episode_count': self.episode_count,
            'epsilon': self.epsilon,
            'q_table_size': len(self.q_table),
            'avg_reward_per_episode': self.total_reward / max(1, self.episode_count)
        }

# Example usage and integration functions
def create_smart_traffic_controller():
    """Factory function to create a configured RL agent"""
    agent = TrafficRLAgent(
        learning_rate=0.15,
        discount_factor=0.9,
        epsilon=0.2
    )
    
    # Try to load existing model
    agent.load_model('models/checkpoints/traffic_rl_model.pkl')
    
    return agent

def simulate_training_episode(agent: TrafficRLAgent, steps=1000):
    """
    Simulate a training episode for the RL agent
    This would normally be integrated with the actual traffic simulation
    """
    total_reward = 0
    
    for step in range(steps):
        # Simulate random traffic state
        vehicle_counts = {
            'north': random.randint(0, 10),
            'east': random.randint(0, 10),
            'south': random.randint(0, 10),
            'west': random.randint(0, 10)
        }
        
        current_green = random.randint(0, 3)
        emergency_present = random.random() < 0.05
        
        # Get state and action
        state = agent.get_state(vehicle_counts, current_green, emergency_present)
        action = agent.get_action(state)
        
        # Simulate environment response
        waiting_times = {dir: random.uniform(5, 30) for dir in ['north', 'east', 'south', 'west']}
        reward = agent.calculate_reward(vehicle_counts, waiting_times, emergency_present and action == ActionType.EMERGENCY_OVERRIDE)
        
        # Simulate next state
        next_vehicle_counts = {k: max(0, v + random.randint(-2, 3)) for k, v in vehicle_counts.items()}
        next_state = agent.get_state(next_vehicle_counts, (current_green + 1) % 4, False)
        
        # Update Q-table
        agent.update_q_table(state, action, reward, next_state)
        total_reward += reward
    
    agent.episode_count += 1
    agent.decay_epsilon()
    
    return total_reward