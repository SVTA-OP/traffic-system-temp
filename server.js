const express = require('express');
const path = require('path');

const app = express();
const PORT = 5000;

// Middleware to disable caching for development
app.use((req, res, next) => {
  res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
  res.setHeader('Pragma', 'no-cache');
  res.setHeader('Expires', '0');
  next();
});

// Serve static files from frontend/web_sim
app.use(express.static(path.join(__dirname, 'frontend', 'web_sim')));

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
    timestamp: new Date().toISOString()
  };
  
  res.json(trafficData);
});

// Catch all handler for SPA
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'web_sim', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Smart Traffic Management Simulation server running on http://0.0.0.0:${PORT}`);
});