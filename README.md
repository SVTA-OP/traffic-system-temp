# Smart Traffic Management Simulation

A comprehensive AI-powered traffic control system developed for the Smart India Hackathon. This project demonstrates intelligent traffic management through real-time vehicle detection, machine learning-based optimization, and dynamic traffic light control using computer vision, reinforcement learning, and web-based visualization.

## 🏗️ System Architecture

- **Frontend**: Canvas-based web simulation with HTML5, CSS3, and JavaScript
- **Backend**: Dual approach with Express.js server and Python Flask application
- **AI Components**: Pygame-based traffic simulation with reinforcement learning
- **Hardware Integration**: Arduino and Raspberry Pi support for IoT prototyping

## 📋 Requirements

### Software Prerequisites
- **Node.js** (v16 or higher)
- **Python** (v3.11 or higher)
- **Git**

### System Dependencies (for Pygame)
- SDL2 development libraries
- Audio and graphics libraries

## 🚀 Setup Instructions for VS Code

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd smart-traffic-management-simulation
```

### 2. Install System Dependencies

#### On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3-dev python3-pip nodejs npm
sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
sudo apt install libfreetype6-dev libportmidi-dev libjpeg-dev libpng-dev
```

#### On macOS:
```bash
# Install Homebrew if you haven't already
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 node npm
brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf
brew install freetype portmidi jpeg libpng
```

#### On Windows:
1. Install [Node.js](https://nodejs.org/) from the official website
2. Install [Python 3.11+](https://python.org/) from the official website
3. Pygame should install automatically with pip (includes SDL2 binaries)

### 3. Install Python Dependencies
```bash
# Create and activate virtual environment (recommended)
python3 -m venv traffic_env
source traffic_env/bin/activate  # On Windows: traffic_env\Scripts\activate

# Install Python packages
pip install -r requirements.txt
```

### 4. Install Node.js Dependencies
```bash
npm install
```

### 5. Project Structure
```
smart-traffic-sim/
├── README.md
├── LICENSE
├── requirements.txt
├── package.json
├── server.js
├── .gitignore
├── docs/
│   ├── DESIGN.md
│   └── PROMPTS.md
├── frontend/
│   └── web_sim/
│       ├── index.html
│       ├── styles.css
│       └── app.js
├── backend/
│   ├── flask_app/
│   │   ├── app.py
│   │   └── rl_agent.py
├── models/
│   ├── yolov8/
│   └── checkpoints/
├── notebooks/
│   └── train_detector.ipynb
├── prototype/
│   ├── arduino/
│   │   └── traffic_controller.ino
│   └── raspberry_pi/
│       └── pi_reader.py
├── demo_video.mp4
└── tests/
```

## 🎮 Running the Application

### Method 1: Run Both Components Separately

#### Terminal 1 - Start the Web Server:
```bash
npm start
```
This starts the Express.js server on `http://localhost:5000`

#### Terminal 2 - Start the Pygame Simulation:
```bash
cd backend/flask_app
python app.py
```

### Method 2: Using VS Code Tasks (Recommended)

1. Open the project in VS Code
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
3. Type "Tasks: Run Task"
4. Select either:
   - "Start Web Server" 
   - "Start Traffic Simulation"
   - "Start Both Services"

### Method 3: Using Package Scripts
```bash
# Start web server only
npm run start

# Start development mode
npm run dev
```

### Method 4: Testing the Scheduling System
```bash
# Run the scheduling algorithm tests
cd backend/flask_app
python -m pytest ../../tests/test_schedulers.py -v

# Test individual scheduling algorithms
python -c "
from schedulers import TrafficScheduler, IntersectionState, SchedulingPolicy
scheduler = TrafficScheduler()
state = IntersectionState(
    queues={'N': 5, 'E': 3, 'S': 2, 'W': 4},
    waiting_times={'N': [10,15,20,25,30], 'E': [5,8,12], 'S': [7,9], 'W': [18,22,25,28]},
    arrival_rates={'N': 0.1, 'E': 0.05, 'S': 0.03, 'W': 0.08},
    emergency=[], current_phase='NS_green', sim_time=100.0
)
plan = scheduler.schedule(state, SchedulingPolicy.META)
print('Generated schedule:', [f'{p.phase}: {p.duration}s' for p in plan])
"
```

## 🎯 Usage Instructions

### Web Interface
1. Open your browser and navigate to `http://localhost:5000`
2. Use the interactive dashboard to:
   - Monitor real-time traffic data
   - View intersection statistics
   - Control simulation parameters

### Pygame Simulation Controls
- **SPACE**: Spawn emergency vehicle
- **1-4**: Spawn vehicle in specific lane (North, East, South, West)
- **ESC**: Exit simulation

### Features
- **Dynamic Traffic Lights**: AI-controlled timing based on vehicle density
- **Emergency Vehicle Priority**: Automatic green light for emergency vehicles
- **Real-time Statistics**: Vehicle count, wait times, and flow metrics
- **Multi-lane Intersection**: 4-way crossroad simulation

## 🔧 Development

### VS Code Extensions (Recommended)
- Python
- JavaScript (ES6) code snippets
- Live Server
- GitLens
- Prettier - Code formatter

### Debugging
- Python simulation can be debugged using VS Code's Python debugger
- Web interface can be debugged using browser developer tools
- Use `console.log()` for JavaScript debugging

## 🏆 Smart India Hackathon Features

### AI/ML Components
- **Reinforcement Learning**: Q-learning for traffic optimization
- **Computer Vision**: Vehicle detection (YOLOv8 integration planned)
- **Predictive Analytics**: Traffic flow optimization

### Hardware Integration
- **Arduino**: Traffic light controller prototype
- **Raspberry Pi**: Camera-based vehicle detection
- **IoT Integration**: Real-time sensor data processing

## 📊 Project Components

### Frontend (`frontend/web_sim/`)
- Interactive traffic visualization
- Real-time dashboard
- Canvas-based animation

### Backend (`backend/flask_app/`)
- Pygame traffic simulation
- AI traffic light controller
- Vehicle physics engine

### Models (`models/`)
- YOLOv8 vehicle detection
- Trained model checkpoints
- ML model artifacts

### Prototype (`prototype/`)
- Arduino traffic controller
- Raspberry Pi integration
- Hardware interface code

## 🐛 Troubleshooting

### Common Issues

#### Pygame Installation Issues:
```bash
# If pygame fails to install, try:
pip install pygame --upgrade
# Or on Linux:
sudo apt install python3-pygame
```

#### Port Already in Use:
```bash
# Kill process using port 5000
sudo lsof -t -i tcp:5000 | xargs kill -9
# Or change port in server.js
```

#### SDL2 Errors on Linux:
```bash
# Install additional SDL2 packages
sudo apt install libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For questions and support, please refer to the documentation in the `docs/` directory or create an issue on the repository.

---
**Smart India Hackathon 2024** | AI-Powered Traffic Management Solution

**Languages Used**:
- Python
- JavaScript
- HTML
- CSS

**Packages Used**:
- **Python**: pygame, flask, numpy, opencv-python, tensorflow (for potential future ML integration), pytest
- **JavaScript**: express, socket.io, react (for frontend framework, if applicable)