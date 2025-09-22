class TrafficSimulation {
    constructor() {
        this.isRunning = false;
        this.animationId = null;
        this.canvas = document.getElementById('trafficCanvas');
        this.ctx = this.canvas.getContext('2d');

        // Canvas settings
        this.canvasWidth = 800;
        this.canvasHeight = 600;
        this.canvas.width = this.canvasWidth;
        this.canvas.height = this.canvasHeight;

        // Intersection settings
        this.centerX = this.canvasWidth / 2;
        this.centerY = this.canvasHeight / 2;
        this.roadWidth = 120;
        this.laneWidth = 30;

        // Simulation state
        this.vehicles = [];
        this.emergencyVehicles = [];
        this.emergencyQueue = []; // FCFS queue for emergency vehicles
        this.preemptionState = 'normal'; // 'normal', 'yellow', 'allred', 'emergency'
        this.allRedTimer = 0;
        this.allRedDuration = 1000; // 1 second all-red clearance
        this.lastSpawnTime = 0;
        this.lastEmergencySpawn = 0;
        this.spawnRate = 2000; // milliseconds between spawns
        this.emergencyRate = 15000; // emergency vehicle every 15 seconds
        
        // Vehicle spacing constants
        this.minGapSpawn = 40; // minimum gap for spawning
        this.minGapMove = 25; // minimum gap between moving vehicles
        this.maxDeceleration = 0.1; // maximum deceleration for stopping

        // Traffic light system
        this.trafficLights = [
            { direction: 'North', x: this.centerX - 15, y: this.centerY - 80, state: 'red', timer: 0, carCount: 0 },
            { direction: 'East', x: this.centerX + 80, y: this.centerY - 15, state: 'red', timer: 0, carCount: 0 },
            { direction: 'South', x: this.centerX + 15, y: this.centerY + 80, state: 'red', timer: 0, carCount: 0 },
            { direction: 'West', x: this.centerX - 80, y: this.centerY + 15, state: 'red', timer: 0, carCount: 0 }
        ];

        this.currentGreenIndex = 0;
        this.trafficLights[0].state = 'green';
        this.lightChangeTime = 0;
        this.yellowTime = 2000;
        this.minGreenTime = 4000;
        this.maxGreenTime = 10000;

        // Stats
        this.stats = {
            totalVehicles: 0,
            vehiclesPassed: 0,
            emergencyVehicles: 0,
            currentWaiting: 0
        };

        this.initializeEventListeners();
        this.addLog('🚦 Smart Traffic Management System Ready!');
    }

    initializeEventListeners() {
        document.getElementById('startBtn').addEventListener('click', () => this.startSimulation());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopSimulation());
        document.getElementById('resetBtn').addEventListener('click', () => this.resetSimulation());

        // Manual controls
        document.addEventListener('keydown', (e) => {
            if (!this.isRunning) return;
            switch(e.key.toLowerCase()) {
                case '1':
                    this.spawnVehicle(0); // North
                    break;
                case '2':
                    this.spawnVehicle(1); // East
                    break;
                case '3':
                    this.spawnVehicle(2); // South
                    break;
                case '4':
                    this.spawnVehicle(3); // West
                    break;
                case '5': // Emergency vehicle from North
                    this.spawnEmergencyVehicle(0);
                    break;
                case '6': // Emergency vehicle from East
                    this.spawnEmergencyVehicle(1);
                    break;
                case '7': // Emergency vehicle from South
                    this.spawnEmergencyVehicle(2);
                    break;
                case '8': // Emergency vehicle from West
                    this.spawnEmergencyVehicle(3);
                    break;
            }
        });
    }

    spawnVehicle(direction) {
        // Check if safe to spawn (no stacking)
        const safeOffset = this.findSafeSpawnPosition(direction);
        if (safeOffset === -1) {
            return; // Cannot spawn safely, skip this spawn
        }

        const directions = ['North', 'East', 'South', 'West'];
        const colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'];

        let startX, startY, targetX, targetY, angle;

        switch(direction) {
            case 0: // North (coming from south)
                startX = this.centerX - 15;
                startY = this.canvasHeight + safeOffset;
                targetX = this.centerX - 15;
                targetY = -30;
                angle = -Math.PI / 2;
                break;
            case 1: // East (coming from west)
                startX = -30 - safeOffset;
                startY = this.centerY - 15;
                targetX = this.canvasWidth + 30;
                targetY = this.centerY - 15;
                angle = 0;
                break;
            case 2: // South (coming from north)
                startX = this.centerX + 15;
                startY = -30 - safeOffset;
                targetX = this.centerX + 15;
                targetY = this.canvasHeight + 30;
                angle = Math.PI / 2;
                break;
            case 3: // West (coming from east)
                startX = this.canvasWidth + 30 + safeOffset;
                startY = this.centerY + 15;
                targetX = -30;
                targetY = this.centerY + 15;
                angle = Math.PI;
                break;
        }

        const vehicle = {
            x: startX,
            y: startY,
            targetX: targetX,
            targetY: targetY,
            direction: direction,
            directionName: directions[direction],
            speed: 1.5 + Math.random() * 0.5,
            maxSpeed: 1.5 + Math.random() * 0.5,
            currentSpeed: 0,
            color: colors[Math.floor(Math.random() * colors.length)],
            width: 20,
            height: 12,
            angle: angle,
            stopped: false,
            isEmergency: false,
            id: Math.random().toString(36).substr(2, 9)
        };

        this.vehicles.push(vehicle);
        this.stats.totalVehicles++;
        this.updateStats();
    }

    spawnEmergencyVehicle(direction = null) {
        // If no specific direction given, pick random
        if (direction === null) {
            direction = Math.floor(Math.random() * 4);
        }
        const originalLength = this.vehicles.length;
        this.spawnVehicle(direction);

        // Check if vehicle was actually spawned
        if (this.vehicles.length > originalLength) {
            // Convert last spawned vehicle to emergency
            const lastVehicle = this.vehicles[this.vehicles.length - 1];
            lastVehicle.isEmergency = true;
            lastVehicle.color = '#ff0000';
            lastVehicle.speed *= 1.3;
            lastVehicle.maxSpeed *= 1.3;

            // Add to emergency queue for FCFS handling
            const emergencyRequest = {
                direction: direction,
                timestamp: Date.now(),
                vehicleId: lastVehicle.id
            };
            
            // Add to queue (allow multiple emergencies per direction)
            this.emergencyQueue.push(emergencyRequest);
            // Sort by timestamp to maintain FCFS order
            this.emergencyQueue.sort((a, b) => a.timestamp - b.timestamp);

            this.stats.emergencyVehicles++;
            this.addLog(`🚨 Emergency vehicle approaching from ${lastVehicle.directionName}!`, 'warning');
            this.updateStats();
        }
    }

    updateTrafficLights(deltaTime) {
        // Count vehicles waiting at each direction
        this.trafficLights.forEach((light, index) => {
            light.carCount = this.countVehiclesWaiting(index);
        });

        // Check for new emergency vehicles and add to queue
        this.checkAndAddEmergencyRequests();

        // FCFS Emergency vehicle preemption system
        if (this.emergencyQueue.length > 0 && this.preemptionState === 'normal') {
            const nextEmergencyRequest = this.emergencyQueue[0];
            if (this.currentGreenIndex !== nextEmergencyRequest.direction) {
                this.addLog(`🚨 Emergency preemption: FCFS switching to ${this.trafficLights[nextEmergencyRequest.direction].direction}`, 'warning');
                this.startEmergencyPreemption(nextEmergencyRequest.direction);
                return;
            } else {
                // Emergency is from current green direction - hold green
                this.preemptionState = 'emergency';
                this.addLog(`🚨 Emergency vehicle detected in current green direction - holding green`);
            }
        }

        // Handle preemption state machine
        if (this.preemptionState === 'yellow') {
            this.lightChangeTime += deltaTime;
            if (this.lightChangeTime >= this.yellowTime) {
                this.preemptionState = 'allred';
                this.allRedTimer = 0;
                this.trafficLights.forEach(light => light.state = 'red');
                this.addLog('🔴 All-red clearance phase for emergency vehicle');
            }
        } else if (this.preemptionState === 'allred') {
            this.allRedTimer += deltaTime;
            if (this.allRedTimer >= this.allRedDuration) {
                const emergencyRequest = this.emergencyQueue[0];
                this.trafficLights[emergencyRequest.direction].state = 'green';
                this.currentGreenIndex = emergencyRequest.direction;
                this.preemptionState = 'emergency';
                this.lightChangeTime = 0;
                this.addLog(`💚 Emergency green: ${this.trafficLights[emergencyRequest.direction].direction}`);
            }
        } else if (this.preemptionState === 'emergency') {
            // Check if emergency vehicle has cleared intersection
            if (this.hasEmergencyVehicleCleared()) {
                this.emergencyQueue.shift(); // Remove served request
                this.preemptionState = 'normal';
                this.lightChangeTime = 0;
                this.addLog('✅ Emergency vehicle cleared, returning to normal operation');
            }
        }

        // Normal traffic light operation
        if (this.preemptionState === 'normal') {
            this.lightChangeTime += deltaTime;

            // Dynamic green time based on vehicle count
            const currentLight = this.trafficLights[this.currentGreenIndex];
            let greenDuration = this.minGreenTime + (currentLight.carCount * 1000);
            greenDuration = Math.min(greenDuration, this.maxGreenTime);

            // Check if we should switch to yellow
            if (currentLight.state === 'green' && this.lightChangeTime >= greenDuration) {
                currentLight.state = 'yellow';
                currentLight.timer = 0;
                this.addLog(`💛 ${currentLight.direction} switching to yellow`);
            }

            // Check if we should switch to next direction
            if (currentLight.state === 'yellow') {
                currentLight.timer += deltaTime;
                if (currentLight.timer >= this.yellowTime) {
                    this.switchToNextDirection();
                }
            }
        }
    }

    countVehiclesWaiting(direction) {
        let count = 0;
        this.vehicles.forEach(vehicle => {
            if (vehicle.direction === direction && vehicle.stopped) {
                count++;
            }
        });
        return count;
    }

    checkAndAddEmergencyRequests() {
        // Check for emergency vehicles near intersection and add to queue if not already present
        for (let vehicle of this.vehicles) {
            if (vehicle.isEmergency && this.isVehicleNearIntersection(vehicle)) {
                const existingRequest = this.emergencyQueue.find(req => req.vehicleId === vehicle.id);
                if (!existingRequest) {
                    this.emergencyQueue.push({
                        direction: vehicle.direction,
                        timestamp: Date.now(),
                        vehicleId: vehicle.id
                    });
                    // Sort by timestamp to maintain FCFS order
                    this.emergencyQueue.sort((a, b) => a.timestamp - b.timestamp);
                }
            }
        }
        
        // Clean up queue - remove requests for vehicles that no longer exist
        this.emergencyQueue = this.emergencyQueue.filter(req => 
            this.vehicles.find(v => v.id === req.vehicleId)
        );
    }

    startEmergencyPreemption(emergencyDirection) {
        this.preemptionState = 'yellow';
        this.trafficLights[this.currentGreenIndex].state = 'yellow';
        this.trafficLights[this.currentGreenIndex].timer = 0;
        this.lightChangeTime = 0;
    }

    hasEmergencyVehicleCleared() {
        if (this.emergencyQueue.length === 0) return true;
        
        const currentRequest = this.emergencyQueue[0];
        const emergencyVehicle = this.vehicles.find(v => v.id === currentRequest.vehicleId);
        
        // If emergency vehicle no longer exists, it has cleared
        if (!emergencyVehicle) return true;
        
        // Check if emergency vehicle has passed through intersection
        const hasPassedIntersection = this.hasVehiclePassedIntersection(emergencyVehicle);
        return hasPassedIntersection;
    }

    hasVehiclePassedIntersection(vehicle) {
        const centerX = this.centerX;
        const centerY = this.centerY;
        
        switch (vehicle.direction) {
            case 0: // North - going up
                return vehicle.y < centerY - 60;
            case 1: // East - going right
                return vehicle.x > centerX + 60;
            case 2: // South - going down
                return vehicle.y > centerY + 60;
            case 3: // West - going left
                return vehicle.x < centerX - 60;
        }
        return false;
    }

    isVehicleNearIntersection(vehicle) {
        const distance = Math.sqrt(
            Math.pow(vehicle.x - this.centerX, 2) + 
            Math.pow(vehicle.y - this.centerY, 2)
        );
        return distance < 100;
    }

    switchLight(newDirection) {
        // Set all lights to red
        this.trafficLights.forEach(light => light.state = 'red');

        // Set new direction to green
        this.trafficLights[newDirection].state = 'green';
        this.currentGreenIndex = newDirection;
        this.lightChangeTime = 0;

        this.addLog(`💚 ${this.trafficLights[newDirection].direction} light is now GREEN`);
    }

    switchToNextDirection() {
        this.trafficLights[this.currentGreenIndex].state = 'red';

        // Find next direction with most vehicles or cycle through
        let nextDirection = (this.currentGreenIndex + 1) % 4;
        let maxCars = 0;
        let bestDirection = nextDirection;

        for (let i = 0; i < 4; i++) {
            if (this.trafficLights[i].carCount > maxCars) {
                maxCars = this.trafficLights[i].carCount;
                bestDirection = i;
            }
        }

        // Use best direction if it has waiting vehicles, otherwise cycle
        this.currentGreenIndex = maxCars > 0 ? bestDirection : nextDirection;
        this.trafficLights[this.currentGreenIndex].state = 'green';
        this.lightChangeTime = 0;

        this.addLog(`💚 Switched to ${this.trafficLights[this.currentGreenIndex].direction} (${maxCars} vehicles waiting)`);
    }

    updateVehicles(deltaTime) {
        // Use reverse iteration to safely remove vehicles
        for (let i = this.vehicles.length - 1; i >= 0; i--) {
            const vehicle = this.vehicles[i];

            // Check if vehicle should stop at red light
            const light = this.trafficLights[vehicle.direction];
            const shouldStopForLight = this.shouldVehicleStop(vehicle, light);
            
            // Car-following behavior: check for vehicle ahead
            const vehicleAhead = this.findVehicleAhead(vehicle);
            const shouldStopForVehicle = vehicleAhead && this.getDistanceToVehicle(vehicle, vehicleAhead) < this.minGapMove;
            
            const shouldStop = shouldStopForLight || shouldStopForVehicle;
            vehicle.stopped = shouldStop;

            if (!shouldStop) {
                // Smooth acceleration/deceleration
                if (vehicle.currentSpeed < vehicle.maxSpeed) {
                    vehicle.currentSpeed = Math.min(vehicle.maxSpeed, vehicle.currentSpeed + 0.05);
                }
                
                // Move vehicle
                const dx = vehicle.targetX - vehicle.x;
                const dy = vehicle.targetY - vehicle.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance > 5) {
                    vehicle.x += (dx / distance) * vehicle.currentSpeed;
                    vehicle.y += (dy / distance) * vehicle.currentSpeed;
                } else {
                    // Vehicle has reached destination - safe to remove
                    this.vehicles.splice(i, 1);
                    this.stats.vehiclesPassed++;
                }
            } else {
                // Smooth deceleration when stopping
                vehicle.currentSpeed = Math.max(0, vehicle.currentSpeed - this.maxDeceleration);
            }
        }

        // Update waiting count
        this.stats.currentWaiting = this.vehicles.filter(v => v.stopped).length;
        this.updateStats();
    }

    shouldVehicleStop(vehicle, light) {
        if (light.state === 'green') return false;
        // Emergency vehicles now respect lights unless their direction is green
        if (vehicle.isEmergency && light.state !== 'green') return true;

        // Check if vehicle is approaching intersection
        let stopLine;
        switch (vehicle.direction) {
            case 0: // North
                stopLine = this.centerY + 40;
                return vehicle.y > stopLine && vehicle.y < stopLine + 80;
            case 1: // East
                stopLine = this.centerX - 40;
                return vehicle.x < stopLine && vehicle.x > stopLine - 80;
            case 2: // South
                stopLine = this.centerY - 40;
                return vehicle.y < stopLine && vehicle.y > stopLine - 80;
            case 3: // West
                stopLine = this.centerX + 40;
                return vehicle.x > stopLine && vehicle.x < stopLine + 80;
        }
        return false;
    }

    findVehicleAhead(vehicle) {
        const vehiclesInSameDirection = this.vehicles.filter(v => 
            v.direction === vehicle.direction && v.id !== vehicle.id
        );

        let closestVehicle = null;
        let minDistance = Infinity;

        vehiclesInSameDirection.forEach(otherVehicle => {
            const distance = this.getDistanceToVehicle(vehicle, otherVehicle);
            if (distance > 0 && distance < minDistance && this.isVehicleAhead(vehicle, otherVehicle)) {
                minDistance = distance;
                closestVehicle = otherVehicle;
            }
        });

        return closestVehicle;
    }

    getDistanceToVehicle(vehicle1, vehicle2) {
        return Math.sqrt(
            Math.pow(vehicle1.x - vehicle2.x, 2) + 
            Math.pow(vehicle1.y - vehicle2.y, 2)
        );
    }

    isVehicleAhead(vehicle, otherVehicle) {
        switch (vehicle.direction) {
            case 0: // North - going up, ahead means lower y
                return otherVehicle.y < vehicle.y;
            case 1: // East - going right, ahead means higher x
                return otherVehicle.x > vehicle.x;
            case 2: // South - going down, ahead means higher y
                return otherVehicle.y > vehicle.y;
            case 3: // West - going left, ahead means lower x
                return otherVehicle.x < vehicle.x;
        }
        return false;
    }

    draw() {
        // Clear canvas
        this.ctx.fillStyle = '#2c3e50';
        this.ctx.fillRect(0, 0, this.canvasWidth, this.canvasHeight);

        // Draw roads
        this.drawRoads();

        // Draw traffic lights
        this.drawTrafficLights();

        // Draw vehicles
        this.drawVehicles();

        // Draw UI elements
        this.drawUI();
    }

    drawRoads() {
        this.ctx.fillStyle = '#34495e';

        // Horizontal road
        this.ctx.fillRect(0, this.centerY - this.roadWidth/2, this.canvasWidth, this.roadWidth);

        // Vertical road
        this.ctx.fillRect(this.centerX - this.roadWidth/2, 0, this.roadWidth, this.canvasHeight);

        // Draw lane markings
        this.ctx.strokeStyle = '#f39c12';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([10, 10]);

        // Horizontal lane divider
        this.ctx.beginPath();
        this.ctx.moveTo(0, this.centerY);
        this.ctx.lineTo(this.canvasWidth, this.centerY);
        this.ctx.stroke();

        // Vertical lane divider
        this.ctx.beginPath();
        this.ctx.moveTo(this.centerX, 0);
        this.ctx.lineTo(this.centerX, this.canvasHeight);
        this.ctx.stroke();

        this.ctx.setLineDash([]); // Reset line dash

        // Draw intersection
        this.ctx.fillStyle = '#95a5a6';
        this.ctx.fillRect(
            this.centerX - this.roadWidth/2, 
            this.centerY - this.roadWidth/2, 
            this.roadWidth, 
            this.roadWidth
        );
    }

    drawTrafficLights() {
        this.trafficLights.forEach((light, index) => {
            // Traffic light pole
            this.ctx.fillStyle = '#2c3e50';
            this.ctx.fillRect(light.x - 5, light.y - 30, 10, 60);

            // Traffic light box
            this.ctx.fillStyle = '#34495e';
            this.ctx.fillRect(light.x - 12, light.y - 18, 24, 36);

            // Light circles
            const lightColors = {
                'red': '#e74c3c',
                'yellow': '#f1c40f',
                'green': '#2ecc71'
            };

            // Red light
            this.ctx.fillStyle = light.state === 'red' ? lightColors.red : '#7f8c8d';
            this.ctx.beginPath();
            this.ctx.arc(light.x, light.y - 10, 6, 0, Math.PI * 2);
            this.ctx.fill();

            // Yellow light
            this.ctx.fillStyle = light.state === 'yellow' ? lightColors.yellow : '#7f8c8d';
            this.ctx.beginPath();
            this.ctx.arc(light.x, light.y, 6, 0, Math.PI * 2);
            this.ctx.fill();

            // Green light
            this.ctx.fillStyle = light.state === 'green' ? lightColors.green : '#7f8c8d';
            this.ctx.beginPath();
            this.ctx.arc(light.x, light.y + 10, 6, 0, Math.PI * 2);
            this.ctx.fill();

            // Highlight current green light with glow effect
            if (light.state === 'green') {
                this.ctx.shadowColor = '#2ecc71';
                this.ctx.shadowBlur = 15;
                this.ctx.beginPath();
                this.ctx.arc(light.x, light.y + 10, 8, 0, Math.PI * 2);
                this.ctx.strokeStyle = '#2ecc71';
                this.ctx.lineWidth = 3;
                this.ctx.stroke();
                this.ctx.shadowBlur = 0;
            }

            // Timer display
            this.drawTimer(light, index);

            // Enhanced direction label with better visibility
            this.ctx.fillStyle = '#ffffff';
            this.ctx.font = 'bold 16px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.strokeStyle = '#2c3e50';
            this.ctx.lineWidth = 3;
            
            // Draw background for better contrast
            const labelText = light.direction.toUpperCase();
            const textWidth = this.ctx.measureText(labelText).width;
            this.ctx.fillStyle = 'rgba(44, 62, 80, 0.8)';
            this.ctx.fillRect(light.x - textWidth/2 - 5, light.y - 55, textWidth + 10, 20);
            
            // Draw the label with outline
            this.ctx.fillStyle = '#ffffff';
            this.ctx.strokeText(labelText, light.x, light.y - 40);
            this.ctx.fillText(labelText, light.x, light.y - 40);

            // Vehicle count
            this.ctx.fillStyle = '#3498db';
            this.ctx.font = '10px Arial';
            this.ctx.fillText(`🚗 ${light.carCount}`, light.x, light.y + 35);
        });
    }

    drawTimer(light, index) {
        let timeRemaining;
        if (light.state === 'green') {
            const greenDuration = this.minGreenTime + (light.carCount * 1000);
            timeRemaining = Math.max(0, greenDuration - this.lightChangeTime);
        } else if (light.state === 'yellow') {
            timeRemaining = Math.max(0, this.yellowTime - light.timer);
        } else {
            timeRemaining = 0;
        }

        const seconds = Math.ceil(timeRemaining / 1000);

        // Timer background
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        this.ctx.fillRect(light.x - 15, light.y - 50, 30, 15);

        // Timer text
        this.ctx.fillStyle = '#ecf0f1';
        this.ctx.font = 'bold 12px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(`${seconds}s`, light.x, light.y - 40);
    }

    drawVehicles() {
        this.vehicles.forEach(vehicle => {
            this.ctx.save();
            this.ctx.translate(vehicle.x, vehicle.y);
            this.ctx.rotate(vehicle.angle);

            // Vehicle body
            this.ctx.fillStyle = vehicle.color;
            this.ctx.fillRect(-vehicle.width/2, -vehicle.height/2, vehicle.width, vehicle.height);

            // Vehicle border
            this.ctx.strokeStyle = '#2c3e50';
            this.ctx.lineWidth = 1;
            this.ctx.strokeRect(-vehicle.width/2, -vehicle.height/2, vehicle.width, vehicle.height);

            // Emergency vehicle effects
            if (vehicle.isEmergency) {
                // Flashing lights
                const flash = Math.floor(Date.now() / 200) % 2;
                this.ctx.fillStyle = flash ? '#ff0000' : '#0000ff';
                this.ctx.fillRect(-vehicle.width/2 - 2, -vehicle.height/2 - 2, 4, 4);
                this.ctx.fillRect(vehicle.width/2 - 2, -vehicle.height/2 - 2, 4, 4);

                // Emergency label
                this.ctx.fillStyle = '#ffffff';
                this.ctx.font = 'bold 8px Arial';
                this.ctx.textAlign = 'center';
                this.ctx.fillText('EMG', 0, 2);
            }

            this.ctx.restore();
        });
    }

    drawUI() {
        // Current green indicator
        const currentLight = this.trafficLights[this.currentGreenIndex];
        this.ctx.fillStyle = 'rgba(46, 204, 113, 0.9)';
        this.ctx.fillRect(10, 10, 200, 40);
        this.ctx.fillStyle = '#ffffff';
        this.ctx.font = 'bold 16px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillText(`🟢 GREEN: ${currentLight.direction}`, 20, 35);

        // Instructions
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        this.ctx.fillRect(10, this.canvasHeight - 80, 300, 70);
        this.ctx.fillStyle = '#ecf0f1';
        this.ctx.font = '12px Arial';
        this.ctx.fillText('🎮 Controls:', 20, this.canvasHeight - 60);
        this.ctx.fillText('🚨 A - Spawn Emergency Vehicle (Ambulance)', 20, this.canvasHeight - 45);
        this.ctx.fillText('🚗 1-4 - Manual Spawn (1=North, 2=East, 3=South, 4=West)', 20, this.canvasHeight - 30);
        this.ctx.fillText('⚡ Auto-spawn and AI traffic control active', 20, this.canvasHeight - 15);
    }

    updateStats() {
        document.getElementById('totalVehicles').textContent = this.stats.totalVehicles;
        document.getElementById('avgWaitTime').textContent = `${this.stats.currentWaiting}`;
        document.getElementById('congestedAreas').textContent = this.stats.emergencyVehicles;

        // Update additional stats in intersections area
        const container = document.getElementById('intersections');
        container.innerHTML = `
            <div class="stat-summary">
                <h3>🚦 Live Traffic Status</h3>
                <div class="traffic-stats">
                    <div class="stat-item">
                        <span class="stat-label">Vehicles Passed:</span>
                        <span class="stat-value">${this.stats.vehiclesPassed}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Currently Waiting:</span>
                        <span class="stat-value">${this.stats.currentWaiting}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Emergency Calls:</span>
                        <span class="stat-value">${this.stats.emergencyVehicles}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Active Green:</span>
                        <span class="stat-value green-indicator">${this.trafficLights[this.currentGreenIndex].direction}</span>
                    </div>
                </div>
            </div>
        `;
    }

    gameLoop(currentTime) {
        if (!this.isRunning) return;

        const deltaTime = currentTime - (this.lastTime || currentTime);
        this.lastTime = currentTime;

        // Auto-spawn vehicles
        if (currentTime - this.lastSpawnTime > this.spawnRate) {
            const direction = Math.floor(Math.random() * 4);
            this.spawnVehicle(direction);
            this.lastSpawnTime = currentTime;
        }

        // Auto-spawn emergency vehicles
        if (currentTime - this.lastEmergencySpawn > this.emergencyRate) {
            this.spawnEmergencyVehicle();
            this.lastEmergencySpawn = currentTime;
        }

        // Update simulation
        this.updateTrafficLights(deltaTime);
        this.updateVehicles(deltaTime);

        // Draw everything
        this.draw();

        this.animationId = requestAnimationFrame((time) => this.gameLoop(time));
    }

    startSimulation() {
        if (this.isRunning) return;

        this.isRunning = true;
        document.getElementById('startBtn').disabled = true;
        document.getElementById('stopBtn').disabled = false;

        this.addLog('🚀 Starting smart traffic simulation...', 'success');
        this.lastTime = performance.now();
        this.gameLoop(this.lastTime);
    }

    stopSimulation() {
        if (!this.isRunning) return;

        this.isRunning = false;
        document.getElementById('startBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;

        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }

        this.addLog('⏹️ Traffic simulation stopped', 'info');
    }

    resetSimulation() {
        this.stopSimulation();

        // Reset all state
        this.vehicles = [];
        this.emergencyVehicles = [];
        this.stats = {
            totalVehicles: 0,
            vehiclesPassed: 0,
            emergencyVehicles: 0,
            currentWaiting: 0
        };

        // Reset traffic lights
        this.trafficLights.forEach((light, index) => {
            light.state = index === 0 ? 'green' : 'red';
            light.timer = 0;
            light.carCount = 0;
        });
        this.currentGreenIndex = 0;
        this.lightChangeTime = 0;

        this.updateStats();
        this.draw();

        document.getElementById('logContainer').innerHTML = '';
        this.addLog('🔄 System reset completed', 'success');
    }

    addLog(message, type = 'info') {
        const logContainer = document.getElementById('logContainer');
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('p');

        let prefix = '';
        switch (type) {
            case 'error':
                prefix = '❌';
                break;
            case 'warning':
                prefix = '⚠️';
                break;
            case 'success':
                prefix = '✅';
                break;
            default:
                prefix = 'ℹ️';
        }

        logEntry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${prefix} ${message}`;
        logEntry.className = `log-entry log-${type}`;
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;

        // Keep only last 15 log entries
        while (logContainer.children.length > 15) {
            logContainer.removeChild(logContainer.firstChild);
        }
    }

    findSafeSpawnPosition(direction) {
        const vehiclesInDirection = this.vehicles.filter(v => v.direction === direction);
        if (vehiclesInDirection.length === 0) return 0;

        // Find the vehicle closest to spawn point
        let closestVehicle = null;
        let minDistance = Infinity;
        
        vehiclesInDirection.forEach(vehicle => {
            let distance;
            switch(direction) {
                case 0: // North - vehicles coming from south
                    distance = this.canvasHeight - vehicle.y;
                    break;
                case 1: // East - vehicles coming from west
                    distance = vehicle.x;
                    break;
                case 2: // South - vehicles coming from north
                    distance = vehicle.y;
                    break;
                case 3: // West - vehicles coming from east
                    distance = this.canvasWidth - vehicle.x;
                    break;
            }
            
            if (distance < minDistance) {
                minDistance = distance;
                closestVehicle = vehicle;
            }
        });
        
        // Return safe distance or indicate no spawn
        return minDistance < this.minGapSpawn ? -1 : 0;
    }
}

// Initialize the simulation when page loads
document.addEventListener('DOMContentLoaded', () => {
    const simulation = new TrafficSimulation();
    simulation.draw(); // Initial draw
});