/*
 * Smart Traffic Light Controller for Arduino
 * Controls physical traffic lights based on sensor input
 */

// Pin definitions
const int LED_RED_NORTH = 2;
const int LED_YELLOW_NORTH = 3;
const int LED_GREEN_NORTH = 4;

const int LED_RED_EAST = 5;
const int LED_YELLOW_EAST = 6;
const int LED_GREEN_EAST = 7;

const int LED_RED_SOUTH = 8;
const int LED_YELLOW_SOUTH = 9;
const int LED_GREEN_SOUTH = 10;

const int LED_RED_WEST = 11;
const int LED_YELLOW_WEST = 12;
const int LED_GREEN_WEST = 13;

// Sensor pins
const int SENSOR_NORTH = A0;
const int SENSOR_EAST = A1;
const int SENSOR_SOUTH = A2;
const int SENSOR_WEST = A3;

// Emergency button
const int EMERGENCY_BTN = A4;

// Timing variables
unsigned long lastSwitchTime = 0;
unsigned long greenDuration = 5000; // 5 seconds default
int currentDirection = 0; // 0=North, 1=East, 2=South, 3=West

// Traffic state
enum LightState {
  RED,
  YELLOW,
  GREEN
};

struct TrafficLight {
  int redPin;
  int yellowPin;
  int greenPin;
  LightState state;
  int vehicleCount;
};

TrafficLight lights[4] = {
  {LED_RED_NORTH, LED_YELLOW_NORTH, LED_GREEN_NORTH, RED, 0},
  {LED_RED_EAST, LED_YELLOW_EAST, LED_GREEN_EAST, RED, 0},
  {LED_RED_SOUTH, LED_YELLOW_SOUTH, LED_GREEN_SOUTH, RED, 0},
  {LED_RED_WEST, LED_YELLOW_WEST, LED_GREEN_WEST, RED, 0}
};

void setup() {
  Serial.begin(9600);
  
  // Initialize LED pins
  for (int i = 0; i < 4; i++) {
    pinMode(lights[i].redPin, OUTPUT);
    pinMode(lights[i].yellowPin, OUTPUT);
    pinMode(lights[i].greenPin, OUTPUT);
  }
  
  // Initialize sensor pins
  pinMode(SENSOR_NORTH, INPUT);
  pinMode(SENSOR_EAST, INPUT);
  pinMode(SENSOR_SOUTH, INPUT);
  pinMode(SENSOR_WEST, INPUT);
  pinMode(EMERGENCY_BTN, INPUT_PULLUP);
  
  // Start with north direction green
  setLightState(0, GREEN);
  Serial.println("Smart Traffic Controller Initialized");
}

void loop() {
  unsigned long currentTime = millis();
  
  // Read vehicle sensors
  readVehicleSensors();
  
  // Check for emergency
  if (digitalRead(EMERGENCY_BTN) == LOW) {
    handleEmergency();
    return;
  }
  
  // Normal traffic light operation
  if (currentTime - lastSwitchTime >= greenDuration) {
    switchToNextDirection();
    lastSwitchTime = currentTime;
  }
  
  // Update light states
  updateLights();
  
  // Send status to serial for monitoring
  sendStatus();
  
  delay(100);
}

void readVehicleSensors() {
  lights[0].vehicleCount = analogRead(SENSOR_NORTH) > 100 ? 1 : 0;
  lights[1].vehicleCount = analogRead(SENSOR_EAST) > 100 ? 1 : 0;
  lights[2].vehicleCount = analogRead(SENSOR_SOUTH) > 100 ? 1 : 0;
  lights[3].vehicleCount = analogRead(SENSOR_WEST) > 100 ? 1 : 0;
}

void setLightState(int direction, LightState state) {
  // Turn off all lights for this direction first
  digitalWrite(lights[direction].redPin, LOW);
  digitalWrite(lights[direction].yellowPin, LOW);
  digitalWrite(lights[direction].greenPin, LOW);
  
  // Set the appropriate light
  switch (state) {
    case RED:
      digitalWrite(lights[direction].redPin, HIGH);
      break;
    case YELLOW:
      digitalWrite(lights[direction].yellowPin, HIGH);
      break;
    case GREEN:
      digitalWrite(lights[direction].greenPin, HIGH);
      break;
  }
  
  lights[direction].state = state;
}

void switchToNextDirection() {
  // Set current direction to yellow, then red
  setLightState(currentDirection, YELLOW);
  delay(2000);
  setLightState(currentDirection, RED);
  
  // Find next direction with vehicles or cycle through
  int nextDirection = (currentDirection + 1) % 4;
  int maxVehicles = 0;
  int bestDirection = nextDirection;
  
  // Smart selection: choose direction with most vehicles
  for (int i = 0; i < 4; i++) {
    if (lights[i].vehicleCount > maxVehicles) {
      maxVehicles = lights[i].vehicleCount;
      bestDirection = i;
    }
  }
  
  // If no vehicles detected, just cycle through
  if (maxVehicles == 0) {
    currentDirection = nextDirection;
  } else {
    currentDirection = bestDirection;
  }
  
  // Set green light for selected direction
  setLightState(currentDirection, GREEN);
  
  // Dynamic green duration based on vehicle count
  greenDuration = max(3000, min(10000, lights[currentDirection].vehicleCount * 2000));
}

void handleEmergency() {
  // Flash all lights and then give priority to emergency direction
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 4; j++) {
      setLightState(j, YELLOW);
    }
    delay(500);
    for (int j = 0; j < 4; j++) {
      setLightState(j, RED);
    }
    delay(500);
  }
  
  // Give green to direction with emergency vehicle
  // For demo, assume emergency is in current direction
  setLightState(currentDirection, GREEN);
  greenDuration = 8000; // Extended green for emergency
  lastSwitchTime = millis();
  
  Serial.println("Emergency Override Activated");
}

void updateLights() {
  // Ensure all non-current directions are red
  for (int i = 0; i < 4; i++) {
    if (i != currentDirection) {
      setLightState(i, RED);
    }
  }
}

void sendStatus() {
  static unsigned long lastStatusTime = 0;
  if (millis() - lastStatusTime >= 1000) { // Send status every second
    Serial.print("Direction: ");
    Serial.print(currentDirection);
    Serial.print(", State: ");
    Serial.print(lights[currentDirection].state);
    Serial.print(", Vehicles: [");
    for (int i = 0; i < 4; i++) {
      Serial.print(lights[i].vehicleCount);
      if (i < 3) Serial.print(",");
    }
    Serial.println("]");
    lastStatusTime = millis();
  }
}