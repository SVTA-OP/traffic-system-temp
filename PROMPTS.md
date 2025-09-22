PROMPTS:

#1:
Build me a Python simulation using Pygame that demonstrates a smart AI traffic light system.
- There should be 4 lanes (like a crossroad) with moving cars represented as rectangles.
- Each lane should have a traffic signal (red, yellow, green).
- Cars should stop when the light is red and move when it is green.
- Green light duration should be dynamic: based on vehicle count in each lane (randomly generated).
- Add an “emergency vehicle” feature: if an ambulance appears in a lane, the light should immediately switch to green for that lane.
- Show real-time updates: vehicle count, current green lane, and timer countdown on the screen.


#2:
Build me a web-based simulation using HTML, CSS, and JavaScript (Canvas).
- Simulate a 4-way intersection with small cars (colored rectangles or icons) moving along roads.
- Each road has a traffic light (red, yellow, green).
- Cars should stop at red and move on green.
- Traffic light timing should be dynamic: adjust green time based on number of cars waiting.
- Randomly spawn cars and occasionally spawn an ambulance that must get priority green.
- Show a timer above each signal and highlight which signal is currently green.
- Keep the interface colorful, simple, and easy to present to non-technical people.


#3:
TASK: Implement a scheduling layer for a traffic intersection simulation. This module will be used by the simulation to produce phase schedules (green cycles + durations). Implement the following:

1) Algorithms to implement:
   a) Round Robin (RR): cycles through directions/phases in fixed order. Duration per phase can be proportional to queue length or fixed.
   b) Shortest Job First (SJF): choose the next phase which will clear the smallest expected remaining 'job' (e.g., vehicles waiting + expected arrivals in short horizon) to reduce average waiting time.
   c) Priority Scheduling: assign priorities by vehicle type + waiting time. Emergency vehicles have highest priority and must preempt schedule. Public transport (if present) higher than private cars; else use waiting time to break ties.
   d) Meta-Scheduler: chooses among RR, SJF, Priority dynamically based on heuristics or rule set:
       - If emergency vehicles present -> always use Priority (immediate preemption).
       - If overall load low (avg queue < low_threshold) -> use RR for simplicity.
       - If high variance in queue lengths -> prefer SJF to reduce backlog.
       - Expose `policy_params` to tune thresholds, minimum green, max green.

2) Interfaces & types (Python):
   - Input type: `IntersectionState` (dict or dataclass) containing:
       queues: Dict[str,int]  # counts per approach: "N","E","S","W"
       waiting_times: Dict[str,List[float]]  # per-vehicle waiting times (seconds)
       arrival_rates: Dict[str,float]  # estimated λ for short horizon (vehicles/sec)
       emergency: List[EmergencyVehicle]  # each has direction, time_to_intersection (ETA seconds), id
       current_phase: str  # e.g., "NS_green" or "EW_green" or "all_red"
       sim_time: float  # current sim time in seconds
   - Output type: `ActionPlan` -> List[Phase], where Phase = {"phase":str, "duration":float, "preemptable":bool}
   - Config: `policy_params` dict containing:
       min_green: float (e.g., 7s)
       max_green: float (e.g., 60s)
       yellow_duration: float (default 3s)
       rr_cycle_order: ["NS_green","EW_green"]
       low_load_threshold: float
       high_variance_threshold: float
       sjf_horizon: float (seconds to forecast arrivals)
       emergency_preempt_buffer: float (seconds to safely transition)

3) Emergency handling:
   - If `emergency` list not empty and any EV ETA <= emergency_preempt_buffer OR already in queue, produce a plan that:
       a) Immediately schedules green for EV direction (with all-red + yellow transitions as required).
       b) Limit preemption duration to clear EVs (configurable).
       c) After EV clears, smoothly resume previously-in-progress scheduling algorithm (remember prior phase and remaining duration).

4) Safety & constraints:
   - Always include yellow/all-red before phase switches (yellow_duration param).
   - Respect min_green & max_green.
   - Avoid frequent oscillations: do not allow same approach to be toggled on/off faster than `min_switch_interval` (configurable).
   - Return deterministic results for same state + params (pure function).

5) Unit tests (pytest):
   - test_rr_basic: verifies RR cycles through phases in the defined order and durations are within limits.
   - test_sjf_reduces_avg_wait: small simulated input where SJF picks shorter job and reduces average waiting time compared to RR.
   - test_emergency_preempt: EV arriving in 4s forces immediate preemption to EV direction; check first phase of action_plan is EV direction.
   - test_meta_switch: when queue variance is high, meta_scheduler selects SJF; when low, selects RR.

6) Logging & metrics:
   - Add optional debug logging (toggle by `debug=True`) that prints chosen policy, reasons (e.g., "high variance -> SJF"), and emergency actions.
   - Provide small helper `explain_decision(state, policy)` that returns a short string explanation for the selection.

7) Integration hooks:
   - Provide `apply_action_plan(sim, action_plan)` stub that shows how the simulation should consume the plan (calls sim.set_phase(phase, duration)).
   - Provide `simulate_one_step(state, action_plan)` example to validate behavior inside unit tests.

8) Code quality:
   - Clear type hints, docstrings, no global state.
   - Keep core logic in functions/classes so Copilot can suggest tests and further optimizations.

Output:
- A single Python module `schedulers.py` with implementations and docstrings
- A `test_schedulers.py` with the 4 unit tests using pytest and a minimal deterministic simulation helper.

Edge cases:
- All queues empty: produce a minimal cyclical RR plan or an empty plan with a small `all_red` pause.
- Multiple simultaneous emergency vehicles from different directions: prioritize the one with smallest ETA; if ETAs equal, pick the one closest to intersection by ETA + direction priority tie-breaker.

Notes for Copilot: produce readable, well-documented code with small helper functions (compute_queue_variance, estimate_jobs_in_horizon, schedule_transition_with_yellow). Use simple deterministic math; no ML required in this module.

