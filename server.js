const express = require('express');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const app = express();
const PORT = 5000;

// Add JSON parsing middleware
app.use(express.json());

// Middleware to disable caching for development
app.use((req, res, next) => {
  res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
  res.setHeader('Pragma', 'no-cache');
  res.setHeader('Expires', '0');
  next();
});

// Serve static files from frontend/web_sim
app.use(express.static(path.join(__dirname, 'frontend', 'web_sim')));

// Global variables for ML integration
let isModelTraining = false;
let lastPrediction = 'Round Robin';
let schedulingAlgorithms = ['Round Robin', 'Priority Scheduling', 'Shortest Job First'];
let ruleViolations = [];
let accidents = [];

// ML prediction function
function getPredictedScheduling(timestamp, carsPresent, emergencyVehicle) {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn('python', [
      'model_training/predict_scheduling.py',
      timestamp,
      carsPresent.toString(),
      emergencyVehicle.toString()
    ]);
    
    let result = '';
    pythonProcess.stdout.on('data', (data) => {
      result += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
      if (code === 0) {
        const prediction = result.trim().split('\n')[0] || 'Round Robin';
        resolve(prediction);
      } else {
        resolve('Round Robin'); // fallback
      }
    });
    
    pythonProcess.on('error', () => {
      resolve('Round Robin'); // fallback
    });
  });
}

// Function to append data to CSV
function appendToDataCSV(timestamp, carsPresent, emergencyVehicle, schedulingModel) {
  const csvLine = `${timestamp},${carsPresent},${emergencyVehicle},${schedulingModel}\n`;
  fs.appendFileSync('model_training/data.csv', csvLine, 'utf8');
  console.log(`[DATA LOG] ${csvLine.trim()}`);
}

// Function to train model
function trainModel() {
  if (isModelTraining) return;
  
  isModelTraining = true;
  console.log('[ML] Starting model training...');
  
  const pythonProcess = spawn('python', ['model_training/tain_model.py'], {
    cwd: process.cwd()
  });
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`[ML TRAIN] ${data.toString().trim()}`);
  });
  
  pythonProcess.stderr.on('data', (data) => {
    console.log(`[ML ERROR] ${data.toString().trim()}`);
  });
  
  pythonProcess.on('close', (code) => {
    isModelTraining = false;
    console.log(`[ML] Model training completed with code ${code}`);
  });
  
  pythonProcess.on('error', (error) => {
    isModelTraining = false;
    console.log(`[ML ERROR] Training failed: ${error.message}`);
  });
}

// Function to detect rule violations
function detectRuleViolations(data) {
  const violations = [];
  
  // Rule 1: Emergency vehicles should get Priority Scheduling
  if (data.emergencyVehicle > 0 && data.schedulingModel !== 'Priority Scheduling') {
    violations.push({
      type: 'Emergency Protocol Violation',
      message: 'Emergency vehicle present but not using Priority Scheduling',
      timestamp: data.timestamp,
      severity: 'HIGH'
    });
  }
  
  // Rule 2: High traffic (>30 cars) should not use Round Robin
  if (data.carsPresent > 30 && data.schedulingModel === 'Round Robin') {
    violations.push({
      type: 'Traffic Congestion Rule Violation',
      message: 'High traffic detected but using inefficient Round Robin',
      timestamp: data.timestamp,
      severity: 'MEDIUM'
    });
  }
  
  // Rule 3: Low traffic (<10 cars) doesn't need Shortest Job First
  if (data.carsPresent < 10 && data.schedulingModel === 'Shortest Job First') {
    violations.push({
      type: 'Resource Optimization Violation',
      message: 'Low traffic but using complex Shortest Job First',
      timestamp: data.timestamp,
      severity: 'LOW'
    });
  }
  
  return violations;
}

// Function to simulate accidents based on conditions
function detectPotentialAccidents(data) {
  const accidents = [];
  
  // High risk scenario: High traffic + Emergency + Wrong scheduling
  if (data.carsPresent > 25 && data.emergencyVehicle > 0 && data.schedulingModel !== 'Priority Scheduling') {
    accidents.push({
      type: 'High Risk Collision Scenario',
      message: 'Emergency vehicle in high traffic without priority - collision risk',
      timestamp: data.timestamp,
      risk: 'CRITICAL',
      action: 'Immediate priority scheduling required'
    });
  }
  
  // Medium risk: Very high traffic with Round Robin
  if (data.carsPresent > 35 && data.schedulingModel === 'Round Robin') {
    accidents.push({
      type: 'Traffic Jam Risk',
      message: 'Severe congestion with inefficient scheduling',
      timestamp: data.timestamp,
      risk: 'HIGH',
      action: 'Switch to Shortest Job First recommended'
    });
  }
  
  return accidents;
}

// API endpoint for traffic data simulation
app.get('/api/traffic-data', (req, res) => {
  // Simulate traffic data
  const trafficData = {
    intersections: [
      {
        id: 1,
        name: 'Main St & 1st Ave',
        vehicles: Math.floor(Math.random() * 20) + 5,
        avgWaitTime: Math.floor(Math.random() * 30) + 10,
        status: Math.random() > 0.7 ? 'congested' : 'normal'
      },
      {
        id: 2,
        name: 'Oak Rd & 2nd Ave',
        vehicles: Math.floor(Math.random() * 15) + 3,
        avgWaitTime: Math.floor(Math.random() * 25) + 8,
        status: Math.random() > 0.8 ? 'congested' : 'normal'
      },
      {
        id: 3,
        name: 'Pine St & 3rd Ave',
        vehicles: Math.floor(Math.random() * 18) + 7,
        avgWaitTime: Math.floor(Math.random() * 35) + 12,
        status: Math.random() > 0.6 ? 'congested' : 'normal'
      }
    ],
    timestamp: new Date().toISOString(),
    currentScheduling: lastPrediction,
    ruleViolations: ruleViolations.slice(-5), // last 5 violations
    accidents: accidents.slice(-3) // last 3 accident risks
  };
  
  res.json(trafficData);
});

// API endpoint to log traffic data
app.post('/api/log-traffic', async (req, res) => {
  try {
    const { carsPresent, emergencyVehicle } = req.body;
    const timestamp = new Date().toISOString();
    
    // Get prediction for current state
    const currentScheduling = await getPredictedScheduling(timestamp, carsPresent, emergencyVehicle);
    lastPrediction = currentScheduling;
    
    // Log to CSV
    appendToDataCSV(timestamp, carsPresent, emergencyVehicle, currentScheduling);
    
    // Check for rule violations
    const violations = detectRuleViolations({ timestamp, carsPresent, emergencyVehicle, schedulingModel: currentScheduling });
    if (violations.length > 0) {
      ruleViolations.push(...violations);
      violations.forEach(v => console.log(`[VIOLATION] ${v.severity}: ${v.message}`));
    }
    
    // Check for accident risks
    const accidentRisks = detectPotentialAccidents({ timestamp, carsPresent, emergencyVehicle, schedulingModel: currentScheduling });
    if (accidentRisks.length > 0) {
      accidents.push(...accidentRisks);
      accidentRisks.forEach(a => console.log(`[ACCIDENT RISK] ${a.risk}: ${a.message} - ${a.action}`));
    }
    
    // Get prediction for 10 seconds ahead
    const futureTimestamp = new Date(Date.now() + 10000).toISOString();
    const futureScheduling = await getPredictedScheduling(futureTimestamp, carsPresent, emergencyVehicle);
    
    console.log(`[TRAFFIC LOG] Cars: ${carsPresent}, Emergency: ${emergencyVehicle}, Current: ${currentScheduling}, Next (10s): ${futureScheduling}`);
    
    res.json({
      success: true,
      currentScheduling,
      futureScheduling,
      violations,
      accidentRisks
    });
  } catch (error) {
    console.error('[ERROR] Failed to log traffic data:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// API endpoint to get latest prediction
app.get('/api/prediction', (req, res) => {
  res.json({ prediction: lastPrediction });
});

// API endpoint to get rule violations
app.get('/api/violations', (req, res) => {
  res.json({ violations: ruleViolations.slice(-10) });
});

// API endpoint to get accident risks
app.get('/api/accidents', (req, res) => {
  res.json({ accidents: accidents.slice(-10) });
});

// Catch all handler for SPA
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'web_sim', 'index.html'));
});

// Start the ML training timer (every 5 seconds)
setInterval(() => {
  // Check if we have enough data to train (at least 5 rows)
  try {
    const csvContent = fs.readFileSync('model_training/data.csv', 'utf8');
    const lines = csvContent.trim().split('\n');
    
    if (lines.length > 5) { // header + at least 5 data rows
      trainModel();
    } else {
      console.log(`[ML] Waiting for more data... (${lines.length - 1} rows available)`);
    }
  } catch (error) {
    console.log('[ML] Waiting for data file to be created...');
  }
}, 5000);

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Smart Traffic Management Simulation server running on http://0.0.0.0:${PORT}`);
  console.log('🚦 AI Traffic Management System Ready!');
  console.log('📊 ML Pipeline: Data logging → Training (5s) → Prediction (10s ahead)');
  console.log('🔍 Monitoring: Rule violations & Accident detection enabled');
  
  // Create data.csv with header if it doesn't exist
  if (!fs.existsSync('model_training/data.csv') || fs.readFileSync('model_training/data.csv', 'utf8').trim() === '') {
    fs.writeFileSync('model_training/data.csv', 'timestamp,cars_present,emergency_vehicle,scheduling_model\n', 'utf8');
    console.log('📝 Created empty data.csv file');
  }
});