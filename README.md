# 🎯 ChronoCore — CPU Scheduling Algorithms Simulator

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![PySide6](https://img.shields.io/badge/PySide6-6.7.0%2B-blue)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

**ChronoCore** is a sophisticated, interactive desktop application for simulating and visualizing CPU scheduling algorithms. It provides both **static** (instant computation) and **live** (real-time simulation) modes, allowing students, educators, and professionals to understand how different scheduling strategies allocate CPU time.

## 🌟 Key Features

### 📊 Four Core Scheduling Algorithms
- **FCFS (First-Come First-Served)** — Non-preemptive, processes execute in arrival order
- **SJF (Shortest Job First)** — Non-preemptive & preemptive (SRTF: Shortest Remaining Time First)
- **Priority Scheduling** — Non-preemptive & preemptive with FCFS tie-breaking
- **Round Robin** — Preemptive, configurable time quantum

### 🎮 Dual Simulation Modes
- **Static Mode** — Instantly compute the entire schedule and display results
- **Live Mode** — Watch the simulation unfold in real-time with 1-second ticks, showing:
  - Current CPU load percentage
  - Active process status
  - Live Gantt chart updates
  - Running metrics (average waiting time, turnaround time)

### 📈 Rich Visualization
- **Gantt Chart** — Color-coded timeline showing CPU allocation by process
- **Process Table** — Track each process with:
  - Process ID, Arrival Time, Burst Time
  - Remaining Time, Priority (if applicable)
  - Status (READY, RUNNING, WAITING, FINISHED)
  - Waiting Time & Turnaround Time
- **Real-Time Metrics** — Average wait time and turnaround time with delta tracking

### ⚙️ Advanced Controls
- **Add Processes Dynamically** — Input processes during setup or even while a live simulation runs
- **Preemptive Toggle** — Switch between preemptive and non-preemptive modes (where applicable)
- **Configurable Quantum** — Set the time slice for Round Robin scheduling
- **Pause/Resume/Stop** — Full playback control in live mode
- **Scenario Reset** — Clear all processes and start fresh

### 💻 Modern UI/UX
- Clean, card-based design with gradient accents
- Responsive layout with sidebar navigation
- Real-time progress bar
- System health indicator
- Contextual status badges

---

## 🏗️ Architecture

### Project Structure

```
ChronoCore/
├── main.py                           # Application entry point
├── requirements.txt                  # Python dependencies
├── LICENSE                           # MIT License
├── README.md                         # Project's Readme file 
├── github                            # CI/CD workflow for builder 
│   ├── workflows
│       └── build-windows-exe.yml
├── assets/                           # Screenshots & images
│   ├── faculty.jpg
│   ├── fcfs.png
│   ├── image.png
│   ├── image copy.png
│   ├── MainWindow.png
│   ├── Priority.png
│   └── sjf.png
│
├── report/                           # Documentation
│   └── chronocore_report.pdf
│
├── scripts/                          # Build utilities
│   └── build_windows_exe.ps1         # PowerShell build script for Windows
│
├── src/
│   ├── Models/                       # Data models & types
│   │   ├── __init__.py
│   │   ├── process.py                # ProcessSpec, ProcessRuntimeState, ProcessStatus
│   │   └── schedule_types.py         # AlgorithmKey, ScheduleResult, SchedulerSnapshot
│   │
│   ├── Controllers/                  # Business logic & orchestration
│   │   ├── __init__.py
│   │   ├── scheduler_controller.py   # Main orchestrator (Qt signals/slots)
│   │   ├── live_runtime.py           # Live simulation state machine
│   │   └── engines/                  # Scheduling algorithm implementations
│   │       ├── __init__.py
│   │       ├── base_engine.py        # Abstract base class
│   │       ├── factory.py            # Engine factory pattern
│   │       ├── fcfs_engine.py        # FCFS implementation
│   │       ├── sjf_engine.py         # SJF/SRTF implementation
│   │       ├── priority_engine.py    # Priority scheduling implementation
│   │       └── rr_engine.py          # Round Robin implementation
│   │
│   └── UI/                           # PySide6 GUI components
│       ├── __init__.py
│       ├── main_window.py            # Root window & layout assembly
│       ├── top_bar.py                # Top control bar (play/pause/stop)
│       ├── sidebar.py                # Left navigation panel
│       ├── input_panel.py            # Process entry form & results
│       ├── active_state_monitor.py   # Process status table
│       ├── gantt_chart.py            # Timeline visualization
│       ├── status_bar.py             # Bottom status indicator
│       └── styles.py                 # Global style constants
│
└── tests/                            # Unit tests
    ├── __init__.py
    ├── test_engines.py               # Engine behavior tests
    └── test_controller_static.py     # Static mode controller tests      
```

### Component Overview

#### **Models** (`src/Models/`)
- **process.py**
  - `ProcessStatus`: Enum (READY, RUNNING, WAITING, FINISHED)
  - `ProcessSpec`: Immutable input definition (PID, arrival, burst, priority)
  - `ProcessRuntimeState`: Mutable state during simulation (remaining time, completion, etc.)

- **schedule_types.py**
  - `AlgorithmKey`: Enum of supported algorithms
  - `TimelineSlice`: Represents one Gantt block
  - `ProcessMetrics`: Computed performance metrics (waiting, turnaround, response time)
  - `ScheduleResult`: Complete schedule with timeline and metrics
  - `SchedulerSnapshot`: Snapshot of live simulation state per tick

#### **Controllers** (`src/Controllers/`)
- **scheduler_controller.py**
  - Central orchestrator bridging UI and scheduling logic
  - Manages mode selection, algorithm changes, process addition
  - Emits Qt signals for UI updates (progress, table updates, results)
  - Handles static and live simulation execution paths

- **live_runtime.py**
  - State machine for per-tick simulation advancement
  - Manages process queues and scheduling decisions
  - Calculates running metrics
  - Supports dynamic process addition during simulation

- **engines/** — Scheduling implementations
  - Each engine extends `BaseSchedulerEngine` with `compute_static()` method
  - Supports both preemptive and non-preemptive modes (where applicable)
  - Returns `ScheduleResult` with timeline, metrics, and statistics

#### **UI** (`src/UI/`)
- **main_window.py**: Root window assembling all child widgets
- **top_bar.py**: Play/pause/stop controls, progress bar, mode selector
- **sidebar.py**: Algorithm selector, preemptive toggle, scenario reset
- **input_panel.py**: Process entry form with conditional fields (priority, quantum)
- **active_state_monitor.py**: Live table showing process states
- **gantt_chart.py**: QPainter-based timeline visualization
- **status_bar.py**: System health indicator, algorithm display, uptime
- **styles.py**: Global color scheme and constants

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Mohamedkhaled687/ChronoCore.git
   cd ChronoCore
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Current dependencies:**
   - `PySide6>=6.7.0` — Qt binding for Python

### Running the Application

```bash
python main.py
```

The application window will launch with a clean, ready-to-use interface.

---

## 📖 Usage Guide

### Step 1: Select Simulation Mode
In the **top bar**, choose between:
- **Static Mode** — Instant complete schedule calculation
- **Live Mode** — Real-time step-by-step simulation

### Step 2: Configure Algorithm & Options
In the **left sidebar**:
1. Select a scheduling algorithm (FCFS, SJF, Priority, Round Robin)
2. Toggle **Preemptive** if applicable to the algorithm
3. View the active algorithm in the status bar

### Step 3: Add Processes
In the **input panel** on the left:
- **Process ID** — Unique identifier (e.g., `P-0001`, `A`, `task-1`)
- **Arrival Time** — When the process arrives (in milliseconds)
- **Burst Time** — How long the process needs CPU time
- **Priority** — (Priority scheduling only) Lower number = higher priority
- **Quantum** — (Round Robin only) Set once per simulation

Click **ADD PROCESS** to add. The form clears automatically for the next entry.

### Step 4: Run the Simulation
Click **RUN SIMULATION** in the top bar:
- **Static mode**: Instant results with complete Gantt chart
- **Live mode**: Animation begins with 1-second ticks

### Step 5: Monitor & Control (Live Mode)
- **Progress bar** shows simulation completion percentage
- **Process table** updates with real-time status
- **Gantt chart** grows as processes are scheduled
- **Metrics display** shows average waiting and turnaround times
- Use **PAUSE**, **RESUME**, or **STOP** buttons to control playback

### Step 6: Review Results
After simulation completion:
- View final Gantt chart
- Inspect per-process metrics (waiting time, turnaround time, response time)
- Average metrics displayed in the input panel

---

## 🎓 Algorithm Details

### FCFS (First-Come First-Served)
- **Mode**: Non-preemptive
- **Behavior**: Processes execute in strict arrival order
- **Pros**: Simple, fair arrival-order guarantee
- **Cons**: High average waiting time if short jobs arrive after long ones (convoy effect)

**Timeline Example:**
```
P1 (4ms) → P2 (3ms) → P3 (1ms)
Gantt: [====P1====][===P2===][P3]
```

### SJF (Shortest Job First) / SRTF (Preemptive)
- **Non-preemptive**: Process with shortest burst time runs to completion
- **Preemptive (SRTF)**: Shorter remaining jobs can interrupt current process
- **Pros**: Minimizes average waiting time (optimal for non-preemptive)
- **Cons**: Unfair to long jobs; requires knowing burst time in advance

**Timeline Example (Preemptive):**
```
P1 (8ms), P2 (4ms) arrives at 1ms, P3 (2ms) arrives at 2ms
Gantt: [P1|P3|P2|P1|P1] → P3 completes first despite arriving last
```

### Priority Scheduling
- **Non-preemptive**: Ready process with highest priority (lowest number) runs
- **Preemptive**: New arrival with higher priority interrupts current process
- **Tie-breaking**: FCFS used to break equal-priority ties
- **Pros**: Important jobs get preferential treatment
- **Cons**: Low-priority jobs may starve indefinitely (aging solution available in future)

**Timeline Example:**
```
P1 (priority=1), P2 (priority=0, arrives at 1ms)
Gantt (preemptive): [P1|P2|P1] → P2 preempts P1 due to higher priority
```

### Round Robin
- **Mode**: Preemptive (always)
- **Behavior**: Processes get fixed time quantum (e.g., 2ms); unfinished processes re-queue
- **Pros**: Fair CPU sharing, good for time-sharing systems
- **Cons**: Higher context-switch overhead; moderate average waiting time

**Timeline Example (Quantum=2ms):**
```
P1 (5ms), P2 (3ms)
Gantt: [P1|P2|P1|P2|P1] → Each gets 2ms turns until finished
```

---

## 🧪 Testing

Run the test suite to verify algorithm correctness:

```bash
pytest tests/
```

**Test Coverage:**
- `test_engines.py` — Algorithm implementations (FCFS order, SJF optimal, preemptive behavior, RR quantum)
- `test_controller_static.py` — Static mode controller orchestration

All tests use deterministic inputs and validate timeline order and metric calculations.

---

## 🎨 UI/UX Design

### Color Scheme
- **Primary**: Teal accents (`#17B890`)
- **Backgrounds**: Clean white cards on light gray (`#F9FAFB`)
- **Text**: Dark gray (`#1F2937`) for primary, medium gray for secondary
- **Status Indicators**: Green (RUNNING), orange (WAITING), gray (FINISHED)

### Layout Hierarchy
```
┌─────────────────────────────────────────┐
│ Top Bar (Mode, Progress, Controls)      │
├────────────┬────────────────────────────┤
│ Sidebar    │ Upper Row                  │
│ (Algo,     │ ├─ Input Panel             │
│  Preset,   │ └─ Active Monitor (Table)  │
│  Options)  │ Lower Row                  │
│            │ └─ Gantt Chart             │
├────────────┴────────────────────────────┤
│ Status Bar (Health, Algorithm, Uptime)  │
└─────────────────────────────────────────┘
```

### Responsive Features
- Splitter between sidebar and content (adjustable width)
- Scrollable Gantt chart for long timelines
- Adaptive table sizing
- Responsive input fields

---

## 🔧 Developer Guide

### Adding a New Scheduling Algorithm

1. **Create engine file** (`src/Controllers/engines/new_algo_engine.py`):
   ```python
   from src.Controllers.engines.base_engine import BaseSchedulerEngine, EngineConfig
   from src.Models import ProcessSpec, ScheduleResult
   
   class NewAlgoEngine(BaseSchedulerEngine):
       def compute_static(self, processes: list[ProcessSpec], config: EngineConfig) -> ScheduleResult:
           timeline = []
           states = self.build_runtime_states(processes)
           
           # Implement your scheduling logic here
           # Use self.append_slice() to add timeline blocks
           # Return self.finalize_result(states, timeline)
           pass
   ```

2. **Register in factory** (`src/Controllers/engines/factory.py`):
   ```python
   class EngineFactory:
       @staticmethod
       def create(algorithm_key: str) -> BaseSchedulerEngine:
           if algorithm_key == "new_algo":
               return NewAlgoEngine()
           # ...
   ```

3. **Add to models** (`src/Models/schedule_types.py`):
   ```python
   class AlgorithmKey(str, Enum):
       # ...
       NEW_ALGO = "new_algo"
   ```

4. **Update sidebar** (`src/UI/sidebar.py`) to include in algorithm list

5. **Add tests** (`tests/test_engines.py`):
   ```python
   def test_new_algo_behavior():
       engine = EngineFactory.create("new_algo")
       # Test your algorithm
   ```

### Extending the UI

UI components use signals/slots for decoupling:
- Emit signals when user actions occur
- Controller connects and processes
- Controller emits result signals
- UI slots update displays

Example: Adding a new metric card
```python
# In InputPanelWidget._build_results_panel():
self.new_metric_card = self._make_metric_card("NEW METRIC", "0.00", "unit")
results_row.addWidget(self.new_metric_card["frame"])

# In controller signal:
self.new_metric_updated.connect(window.input_panel.update_new_metric)

# In update slot:
def update_new_metric(self, value: float) -> None:
    self.new_metric_card["value"].setText(f"{value:.2f}")
```

---

## 📊 Performance Notes

- **Static Mode**: Computation time is negligible even for 1000+ processes
- **Live Mode**: Each tick processes 1 unit time (1 Second); progress updates drive UI refreshes
- **Gantt Chart**: Renders smoothly with 50 pixels/time-unit scaling; horizontal scrolling for long timelines
- **Memory**: Efficient dataclass usage with `slots=True` minimizes memory footprint

---

## 🐛 Known Limitations & Future Enhancements

### Current Limitations
- Live mode simulation is wall-clock time tied to 1-second ticks (not scalable)
- No priority aging in Priority scheduling (risk of starvation)
- Quantum is set globally for all Round Robin processes
- No context-switch overhead simulation

### Planned Enhancements
- [ ] Configurable tick speed (faster/slower simulations)
- [ ] Priority aging to prevent starvation
- [ ] Per-process context-switch cost
- [ ] More scheduling algorithms (MLQ, MLFQ, ...)
- [ ] Process arrival distribution presets (Poisson, uniform, burst)
- [ ] Export results to CSV/JSON
- [ ] Comparison mode (run multiple algorithms side-by-side)
- [ ] Undo/redo for process management

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors & Contributors

**Created by**: Mohamed Khaled  
**Repository**: [github.com/Mohamedkhaled687/ChronoCore](https://github.com/Mohamedkhaled687/ChronoCore)

---

## 📚 References & Resources

### Scheduling Algorithm Background
- Silberschatz, Galvin & Gagne — *Operating System Concepts* (Ch. 6: CPU Scheduling)
- Stallings — *Operating Systems: Internals and Design Principles* (Ch. 9)

### Technical Stack
- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [Python Dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [Qt Signals & Slots Pattern](https://wiki.qt.io/Signals_and_Slots)

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes with clear commit messages
4. Add or update tests as needed
5. Submit a pull request with a description of your changes

---

## 📞 Support & Feedback

- **Issues**: Report bugs via [GitHub Issues](https://github.com/Mohamedkhaled687/ChronoCore/issues)
- **Discussions**: Start conversations in [GitHub Discussions](https://github.com/Mohamedkhaled687/ChronoCore/discussions)
- **Documentation**: See `report/chronocore_report.pdf` for detailed technical documentation

---

<div align="center">

**Made with ❤️ for operating systems students and educators**

⭐ If you find this project helpful, please consider starring the repository!

</div>

---
