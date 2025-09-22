#!/usr/bin/env python3
"""
Raspberry Pi Vehicle Detection Script
Uses camera input to detect vehicles and send data to traffic control system
"""

import cv2
import numpy as np
import time
import json
import requests
from datetime import datetime
import threading
import queue

class VehicleDetector:
    def __init__(self, camera_id=0):
        """Initialize the vehicle detector with camera"""
        self.camera_id = camera_id
        self.cap = None
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True, varThreshold=100
        )
        self.min_area = 500  # Minimum area for vehicle detection
        self.vehicle_count = 0
        self.last_count_time = time.time()
        
        # Detection zones (define 4 lanes)
        self.detection_zones = {
            'north': {'x': 200, 'y': 50, 'w': 100, 'h': 150},
            'east': {'x': 350, 'y': 200, 'w': 150, 'h': 100},
            'south': {'x': 200, 'y': 350, 'w': 100, 'h': 150},
            'west': {'x': 50, 'y': 200, 'w': 150, 'h': 100}
        }
        
        self.vehicle_counts = {'north': 0, 'east': 0, 'south': 0, 'west': 0}
        
    def initialize_camera(self):
        """Initialize camera capture"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                print(f"Error: Could not open camera {self.camera_id}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            print("Camera initialized successfully")
            return True
        except Exception as e:
            print(f"Camera initialization error: {e}")
            return False
    
    def detect_vehicles_in_zone(self, frame, zone_name, zone):
        """Detect vehicles in a specific zone"""
        x, y, w, h = zone['x'], zone['y'], zone['w'], zone['h']
        
        # Extract region of interest
        roi = frame[y:y+h, x:x+w]
        
        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(roi)
        
        # Morphological operations to clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        vehicle_count = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_area:
                vehicle_count += 1
                
                # Draw bounding box on original frame
                x_c, y_c, w_c, h_c = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x + x_c, y + y_c), (x + x_c + w_c, y + y_c + h_c), (0, 255, 0), 2)
        
        return vehicle_count
    
    def process_frame(self, frame):
        """Process a single frame for vehicle detection"""
        if frame is None:
            return None
        
        # Draw detection zones
        for zone_name, zone in self.detection_zones.items():
            x, y, w, h = zone['x'], zone['y'], zone['w'], zone['h']
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(frame, zone_name.upper(), (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        # Detect vehicles in each zone
        for zone_name, zone in self.detection_zones.items():
            count = self.detect_vehicles_in_zone(frame, zone_name, zone)
            self.vehicle_counts[zone_name] = count
            
            # Display count on frame
            x, y = zone['x'], zone['y']
            cv2.putText(frame, f"Vehicles: {count}", (x, y + zone['h'] + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # Display total statistics
        total_vehicles = sum(self.vehicle_counts.values())
        cv2.putText(frame, f"Total Vehicles: {total_vehicles}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, frame.shape[0] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def send_data_to_server(self, server_url="http://localhost:5000/api/vehicle-data"):
        """Send vehicle count data to traffic control server"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'vehicle_counts': self.vehicle_counts,
            'total_vehicles': sum(self.vehicle_counts.values())
        }
        
        try:
            response = requests.post(server_url, json=data, timeout=5)
            if response.status_code == 200:
                print(f"Data sent successfully: {self.vehicle_counts}")
            else:
                print(f"Server error: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send data: {e}")
    
    def run_detection(self, display=True, send_data=True):
        """Main detection loop"""
        if not self.initialize_camera():
            return
        
        print("Starting vehicle detection...")
        print("Press 'q' to quit, 's' to save current frame")
        
        frame_count = 0
        last_data_send = time.time()
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to read frame")
                    break
                
                # Process frame
                processed_frame = self.process_frame(frame)
                
                if display and processed_frame is not None:
                    cv2.imshow('Vehicle Detection', processed_frame)
                
                # Send data every 2 seconds
                if send_data and time.time() - last_data_send >= 2.0:
                    threading.Thread(target=self.send_data_to_server, daemon=True).start()
                    last_data_send = time.time()
                
                frame_count += 1
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    filename = f"traffic_frame_{int(time.time())}.jpg"
                    cv2.imwrite(filename, processed_frame)
                    print(f"Frame saved as {filename}")
                
        except KeyboardInterrupt:
            print("\nDetection stopped by user")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("Resources cleaned up")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Vehicle Detection for Smart Traffic Management')
    parser.add_argument('--camera', type=int, default=0, help='Camera ID (default: 0)')
    parser.add_argument('--no-display', action='store_true', help='Run without display (headless)')
    parser.add_argument('--no-server', action='store_true', help='Don\'t send data to server')
    parser.add_argument('--server-url', type=str, default='http://localhost:5000/api/vehicle-data',
                       help='Server URL for sending data')
    
    args = parser.parse_args()
    
    detector = VehicleDetector(camera_id=args.camera)
    detector.run_detection(
        display=not args.no_display,
        send_data=not args.no_server
    )

if __name__ == "__main__":
    main()