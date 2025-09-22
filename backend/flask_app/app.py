"""
Smart Traffic Management Simulation - Main Application
Pygame-based traffic simulation with AI traffic light control
"""

import pygame
import random
import sys
import time
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional
import math

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# Traffic light states
class LightState(Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"

class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

@dataclass
class Vehicle:
    x: float
    y: float
    direction: Direction
    speed: float
    is_emergency: bool = False
    color: tuple = BLUE
    width: int = 30
    height: int = 15
    
    def __post_init__(self):
        if self.is_emergency:
            self.color = RED
            self.speed *= 1.2  # Emergency vehicles move slightly faster

class TrafficLight:
    def __init__(self, direction: Direction, x: int, y: int):
        self.direction = direction
        self.state = LightState.RED
        self.x = x
        self.y = y
        self.timer = 0
        self.green_duration = 5000  # milliseconds
        self.yellow_duration = 2000
        self.red_duration = 3000
        
    def update(self, dt: int, vehicle_count: int, emergency_present: bool):
        """Update traffic light state based on conditions"""
        # Emergency vehicle overrides normal operation
        if emergency_present and self.state != LightState.GREEN:
            self.state = LightState.GREEN
            self.timer = 0
            return
            
        self.timer += dt
        
        # Dynamic green duration based on vehicle count
        dynamic_green = max(3000, min(10000, vehicle_count * 1000))
        
        if self.state == LightState.GREEN:
            if self.timer >= dynamic_green:
                self.state = LightState.YELLOW
                self.timer = 0
        elif self.state == LightState.YELLOW:
            if self.timer >= self.yellow_duration:
                self.state = LightState.RED
                self.timer = 0
        elif self.state == LightState.RED:
            if self.timer >= self.red_duration:
                self.state = LightState.GREEN
                self.timer = 0
    
    def get_color(self):
        return {
            LightState.RED: RED,
            LightState.YELLOW: YELLOW,
            LightState.GREEN: GREEN
        }[self.state]

class TrafficSimulation:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Smart AI Traffic Light System")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Initialize traffic lights
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        self.traffic_lights = {
            Direction.NORTH: TrafficLight(Direction.NORTH, center_x - 50, center_y - 100),
            Direction.EAST: TrafficLight(Direction.EAST, center_x + 50, center_y - 50),
            Direction.SOUTH: TrafficLight(Direction.SOUTH, center_x + 50, center_y + 100),
            Direction.WEST: TrafficLight(Direction.WEST, center_x - 50, center_y + 50)
        }
        
        # Initialize vehicles
        self.vehicles: Dict[Direction, List[Vehicle]] = {
            Direction.NORTH: [],
            Direction.EAST: [],
            Direction.SOUTH: [],
            Direction.WEST: []
        }
        
        # Timing
        self.last_vehicle_spawn = {direction: 0 for direction in Direction}
        self.current_green_lane = Direction.NORTH
        self.emergency_cooldown = 0
        
        # Stats
        self.stats = {
            'total_vehicles': 0,
            'vehicles_passed': 0,
            'emergency_activations': 0,
            'avg_wait_time': 0
        }
        
        # Set initial green light
        self.traffic_lights[Direction.NORTH].state = LightState.GREEN
        
    def spawn_vehicle(self, direction: Direction):
        """Spawn a new vehicle in the specified direction"""
        current_time = pygame.time.get_ticks()
        
        # Control spawn rate
        if current_time - self.last_vehicle_spawn[direction] < random.randint(1000, 3000):
            return
            
        self.last_vehicle_spawn[direction] = current_time
        
        # 5% chance of emergency vehicle
        is_emergency = random.random() < 0.05
        speed = random.uniform(1, 3)
        
        if direction == Direction.NORTH:
            vehicle = Vehicle(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT - 50, direction, speed, is_emergency)
        elif direction == Direction.EAST:
            vehicle = Vehicle(50, SCREEN_HEIGHT // 2 - 15, direction, speed, is_emergency)
        elif direction == Direction.SOUTH:
            vehicle = Vehicle(SCREEN_WIDTH // 2 + 15, 50, direction, speed, is_emergency)
        else:  # WEST
            vehicle = Vehicle(SCREEN_WIDTH - 50, SCREEN_HEIGHT // 2 + 15, direction, speed, is_emergency)
            
        self.vehicles[direction].append(vehicle)
        self.stats['total_vehicles'] += 1
        
        if is_emergency:
            self.stats['emergency_activations'] += 1
    
    def update_vehicles(self, dt: int):
        """Update all vehicle positions and handle traffic light logic"""
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        stop_distance = 80  # Distance from center to stop
        
        for direction, vehicle_list in self.vehicles.items():
            light = self.traffic_lights[direction]
            emergency_in_lane = any(v.is_emergency for v in vehicle_list)
            
            # Update traffic light
            light.update(dt, len(vehicle_list), emergency_in_lane)
            
            for vehicle in vehicle_list[:]:  # Copy list to avoid modification issues
                should_stop = False
                
                # Check if vehicle should stop at red/yellow light
                if light.state in [LightState.RED, LightState.YELLOW]:
                    if direction == Direction.NORTH and vehicle.y > center_y + stop_distance:
                        should_stop = True
                    elif direction == Direction.EAST and vehicle.x < center_x - stop_distance:
                        should_stop = True
                    elif direction == Direction.SOUTH and vehicle.y < center_y - stop_distance:
                        should_stop = True
                    elif direction == Direction.WEST and vehicle.x > center_x + stop_distance:
                        should_stop = True
                
                # Move vehicle if not stopping
                if not should_stop:
                    if direction == Direction.NORTH:
                        vehicle.y -= vehicle.speed
                    elif direction == Direction.EAST:
                        vehicle.x += vehicle.speed
                    elif direction == Direction.SOUTH:
                        vehicle.y += vehicle.speed
                    else:  # WEST
                        vehicle.x -= vehicle.speed
                
                # Remove vehicles that have passed through
                if (direction == Direction.NORTH and vehicle.y < -50) or \
                   (direction == Direction.EAST and vehicle.x > SCREEN_WIDTH + 50) or \
                   (direction == Direction.SOUTH and vehicle.y > SCREEN_HEIGHT + 50) or \
                   (direction == Direction.WEST and vehicle.x < -50):
                    vehicle_list.remove(vehicle)
                    self.stats['vehicles_passed'] += 1
    
    def draw_road(self):
        """Draw the crossroad"""
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        road_width = 100
        
        # Draw roads
        # Vertical road
        pygame.draw.rect(self.screen, DARK_GRAY, 
                        (center_x - road_width//2, 0, road_width, SCREEN_HEIGHT))
        # Horizontal road
        pygame.draw.rect(self.screen, DARK_GRAY, 
                        (0, center_y - road_width//2, SCREEN_WIDTH, road_width))
        
        # Draw lane dividers
        for i in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.rect(self.screen, WHITE, (center_x - 2, i, 4, 20))
        for i in range(0, SCREEN_WIDTH, 40):
            pygame.draw.rect(self.screen, WHITE, (i, center_y - 2, 20, 4))
        
        # Draw intersection
        pygame.draw.rect(self.screen, GRAY, 
                        (center_x - road_width//2, center_y - road_width//2, 
                         road_width, road_width))
    
    def draw_traffic_lights(self):
        """Draw traffic lights"""
        for light in self.traffic_lights.values():
            # Light post
            pygame.draw.rect(self.screen, BLACK, (light.x - 5, light.y - 20, 10, 40))
            
            # Light box
            pygame.draw.rect(self.screen, BLACK, (light.x - 15, light.y - 15, 30, 30))
            
            # Light
            pygame.draw.circle(self.screen, light.get_color(), (light.x, light.y), 12)
            pygame.draw.circle(self.screen, BLACK, (light.x, light.y), 12, 2)
    
    def draw_vehicles(self):
        """Draw all vehicles"""
        for vehicle_list in self.vehicles.values():
            for vehicle in vehicle_list:
                # Adjust vehicle size based on direction
                if vehicle.direction in [Direction.NORTH, Direction.SOUTH]:
                    width, height = vehicle.width, vehicle.height
                else:
                    width, height = vehicle.height, vehicle.width
                
                rect = pygame.Rect(vehicle.x - width//2, vehicle.y - height//2, width, height)
                pygame.draw.rect(self.screen, vehicle.color, rect)
                pygame.draw.rect(self.screen, BLACK, rect, 2)
                
                # Emergency vehicle indicator
                if vehicle.is_emergency:
                    pygame.draw.circle(self.screen, WHITE, 
                                     (int(vehicle.x), int(vehicle.y)), 5)
    
    def draw_ui(self):
        """Draw user interface with stats and information"""
        # Background panel
        pygame.draw.rect(self.screen, WHITE, (10, 10, 300, 200))
        pygame.draw.rect(self.screen, BLACK, (10, 10, 300, 200), 2)
        
        y_offset = 30
        
        # Title
        title = self.font.render("Traffic Control System", True, BLACK)
        self.screen.blit(title, (20, y_offset))
        y_offset += 40
        
        # Vehicle counts
        for i, (direction, vehicles) in enumerate(self.vehicles.items()):
            count = len(vehicles)
            emergency_count = sum(1 for v in vehicles if v.is_emergency)
            light_state = self.traffic_lights[direction].state.value
            
            text = f"{direction.name}: {count} cars"
            if emergency_count > 0:
                text += f" ({emergency_count} EMG)"
            text += f" - {light_state}"
            
            color = GREEN if light_state == "GREEN" else RED if light_state == "RED" else ORANGE
            vehicle_text = self.small_font.render(text, True, color)
            self.screen.blit(vehicle_text, (20, y_offset))
            y_offset += 25
        
        # Current green lane
        green_lanes = [d.name for d, light in self.traffic_lights.items() if light.state == LightState.GREEN]
        green_text = f"Green Lane: {', '.join(green_lanes) if green_lanes else 'None'}"
        green_surface = self.small_font.render(green_text, True, GREEN)
        self.screen.blit(green_surface, (20, y_offset))
        y_offset += 25
        
        # Stats panel
        stats_bg = pygame.Rect(SCREEN_WIDTH - 220, 10, 200, 120)
        pygame.draw.rect(self.screen, WHITE, stats_bg)
        pygame.draw.rect(self.screen, BLACK, stats_bg, 2)
        
        stats_y = 30
        stats_title = self.small_font.render("Statistics", True, BLACK)
        self.screen.blit(stats_title, (SCREEN_WIDTH - 210, stats_y))
        stats_y += 30
        
        total_text = self.small_font.render(f"Total Vehicles: {self.stats['total_vehicles']}", True, BLACK)
        self.screen.blit(total_text, (SCREEN_WIDTH - 210, stats_y))
        stats_y += 20
        
        passed_text = self.small_font.render(f"Vehicles Passed: {self.stats['vehicles_passed']}", True, BLACK)
        self.screen.blit(passed_text, (SCREEN_WIDTH - 210, stats_y))
        stats_y += 20
        
        emergency_text = self.small_font.render(f"Emergency Calls: {self.stats['emergency_activations']}", True, BLACK)
        self.screen.blit(emergency_text, (SCREEN_WIDTH - 210, stats_y))
        
        # Instructions
        instructions = [
            "A: Spawn emergency vehicle",
            "1-4: Spawn vehicle in lane (N/E/S/W)",
            "ESC: Exit"
        ]
        
        for i, instruction in enumerate(instructions):
            inst_text = self.small_font.render(instruction, True, BLACK)
            self.screen.blit(inst_text, (20, SCREEN_HEIGHT - 80 + i * 20))
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_a:
                    # Spawn emergency vehicle in random lane
                    direction = random.choice(list(Direction))
                    self.spawn_emergency_vehicle(direction)
                elif event.key == pygame.K_1:
                    self.spawn_vehicle(Direction.NORTH)
                elif event.key == pygame.K_2:
                    self.spawn_vehicle(Direction.EAST)
                elif event.key == pygame.K_3:
                    self.spawn_vehicle(Direction.SOUTH)
                elif event.key == pygame.K_4:
                    self.spawn_vehicle(Direction.WEST)
        return True
    
    def spawn_emergency_vehicle(self, direction: Direction):
        """Manually spawn an emergency vehicle"""
        speed = random.uniform(2, 4)
        
        if direction == Direction.NORTH:
            vehicle = Vehicle(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT - 50, direction, speed, True)
        elif direction == Direction.EAST:
            vehicle = Vehicle(50, SCREEN_HEIGHT // 2 - 15, direction, speed, True)
        elif direction == Direction.SOUTH:
            vehicle = Vehicle(SCREEN_WIDTH // 2 + 15, 50, direction, speed, True)
        else:  # WEST
            vehicle = Vehicle(SCREEN_WIDTH - 50, SCREEN_HEIGHT // 2 + 15, direction, speed, True)
            
        self.vehicles[direction].append(vehicle)
        self.stats['total_vehicles'] += 1
        self.stats['emergency_activations'] += 1
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            dt = self.clock.tick(FPS)
            
            # Handle events
            running = self.handle_events()
            
            # Randomly spawn vehicles
            for direction in Direction:
                if random.random() < 0.02:  # 2% chance per frame
                    self.spawn_vehicle(direction)
            
            # Update simulation
            self.update_vehicles(dt)
            
            # Draw everything
            self.screen.fill(GREEN)  # Background (grass)
            self.draw_road()
            self.draw_traffic_lights()
            self.draw_vehicles()
            self.draw_ui()
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    simulation = TrafficSimulation()
    simulation.run()