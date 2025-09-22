# Development Prompts

## Prompt #1
**Initial Project Setup**
"This is a fresh clone of a GitHub import. Lets make it run in the Replit environment. Explore the codebase and understand its core setup (build system, package installer, languages, project layout, etc). Where possible, try to follow existing project setup, databases, APIs, configuration, etc. Make sure both code and config are working."

## Prompt #2
**Project Structure and Pygame Simulation**
"smart-traffic-sim/
├─ README.md
├─ LICENSE
├─ .gitignore
├─ docs/
│  ├─ DESIGN.md
│  └─ PROMPTS.md       <-- store every prompt here (numbered)
├─ frontend/
│  └─ web_sim/          <-- HTML/JS Canvas simulation
│     ├─ index.html
│     ├─ style.css
│     └─ app.js
├─ backend/
│  ├─ flask_app/
│  │  ├─ app.py
│  │  └─ rl_agent.py
├─ models/
│  ├─ yolov8/
│  └─ checkpoints/      <-- store small artifacts or links to HF hub
├─ notebooks/
│  └─ train_detector.ipynb
├─ prototype/
│  ├─ arduino/
│  │  └─ traffic_controller.ino
│  └─ raspberry_pi/
│     └─ pi_reader.py
├─ demo_video.mp4
└─ tests/

THIS MUST BE THE file pathways please....we can add more to this in the future for now chatgpt gave this...

and first : Build me a Python simulation using Pygame that demonstrates a smart AI traffic light system.
- There should be 4 lanes (like a crossroad) with moving cars represented as rectangles.
- Each lane should have a traffic signal (red, yellow, green).
- Cars should stop when the light is red and move when it is green.
- Green light duration should be dynamic: based on vehicle count in each lane (randomly generated).
- Add an "emergency vehicle" feature: if an ambulance appears in a lane, the light should immediately switch to green for that lane.
- Show real-time updates: vehicle count, current green lane, and timer countdown on the screen."