"""Qt-facing scheduler controller orchestrating engines and live runtime."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from src.Controllers.engines import EngineConfig, EngineFactory
from src.Controllers.live_runtime import LiveRuntimeState
from src.Models import AlgorithmKey, ProcessSpec, SimulationMode


class SchedulerController(QObject):
    """Bridge between UI events and backend scheduling logic."""

    progress_updated = Signal(int)
    process_table_updated = Signal(list)
    total_processes_changed = Signal(int)
    cpu_load_changed = Signal(int)
    gantt_block_added = Signal(str, float, float, bool)
    results_updated = Signal(float, float, float, float)
    status_changed = Signal(str)
    system_health_changed = Signal(bool)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.mode = SimulationMode.LIVE
        self.algorithm = AlgorithmKey.FCFS
        self.preemptive = False
        self.quantum = 1.0

        self._processes: list[ProcessSpec] = []
        self._insertion_counter = 0
        self._runtime: Optional[LiveRuntimeState] = None

        self._prev_avg_wait = 0.0
        self._prev_avg_tat = 0.0

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_live_tick)

    # ------------------------------------------------------------------
    # Binding helper
    # ------------------------------------------------------------------
    def bind_window(self, window) -> None:
        """Connect all UI<->controller signals in one place."""
        window.top_bar.run_simulation_clicked.connect(self.start_simulation)
        window.top_bar.stop_simulation_clicked.connect(self.stop_simulation)
        window.top_bar.simulation_mode_changed.connect(self.set_mode)
        window.sidebar.algorithm_selected.connect(self.set_algorithm)
        window.sidebar.preemptive_toggled.connect(self.set_preemptive)
        window.input_panel.process_added.connect(self.add_process)
        window.sidebar.new_scenario_clicked.connect(self.reset_scenario)

        self.progress_updated.connect(window.top_bar.set_progress)
        self.process_table_updated.connect(window.active_monitor.update_process_table)
        self.total_processes_changed.connect(window.active_monitor.set_total_processes)
        self.cpu_load_changed.connect(window.active_monitor.set_cpu_load)
        self.gantt_block_added.connect(window.gantt_chart.add_gantt_block)
        self.results_updated.connect(window.input_panel.update_results)
        self.status_changed.connect(window.input_panel.set_status_badge)
        self.system_health_changed.connect(window.status_bar.set_system_status)

        # Round-Robin quantum rule: lock once running, unlock on reset/finish.
        window.top_bar.run_simulation_clicked.connect(lambda: window.input_panel.set_quantum_locked(True))
        window.sidebar.new_scenario_clicked.connect(lambda: window.input_panel.set_quantum_locked(False))

    # ------------------------------------------------------------------
    # UI slots
    # ------------------------------------------------------------------
    @Slot(str)
    def set_mode(self, mode: str) -> None:
        self.mode = SimulationMode(mode)

    @Slot(str)
    def set_algorithm(self, algorithm: str) -> None:
        self.algorithm = AlgorithmKey(algorithm)

    @Slot(bool)
    def set_preemptive(self, enabled: bool) -> None:
        self.preemptive = enabled

    @Slot(dict)
    def add_process(self, payload: dict) -> None:
        pid = str(payload.get("pid", "")).strip()
        if not pid:
            return

        spec = ProcessSpec(
            pid=pid,
            arrival_time=float(payload.get("arrival", 0.0)),
            burst_time=float(payload.get("burst", 0.0)),
            priority=(int(payload["priority"]) if payload.get("priority") is not None else None),
            insertion_order=self._insertion_counter,
        )
        self._insertion_counter += 1

        if payload.get("quantum") is not None:
            self.quantum = float(payload["quantum"])

        self._processes.append(spec)
        self.total_processes_changed.emit(len(self._processes))

        if self._runtime is not None and self._timer.isActive() and self.mode is SimulationMode.LIVE:
            self._runtime.add_process_live(spec)

    @Slot()
    def start_simulation(self) -> None:
        if not self._processes:
            return

        self.system_health_changed.emit(True)
        self.status_changed.emit("RUNNING")

        if self.mode is SimulationMode.STATIC:
            self._run_static()
            return

        self._runtime = LiveRuntimeState(
            algorithm=self.algorithm,
            preemptive=self.preemptive,
            quantum=self.quantum,
            unit_time=1.0,
            pending_specs=[
                ProcessSpec(
                    pid=p.pid,
                    arrival_time=p.arrival_time,
                    burst_time=p.burst_time,
                    priority=p.priority,
                    insertion_order=p.insertion_order,
                )
                for p in self._processes
            ],
        )
        self._timer.start()

    @Slot()
    def stop_simulation(self) -> None:
        if self._timer.isActive():
            self._timer.stop()
        self.status_changed.emit("READY")
        self.cpu_load_changed.emit(0)

    @Slot()
    def reset_scenario(self) -> None:
        self.stop_simulation()
        self._processes.clear()
        self._runtime = None
        self._insertion_counter = 0
        self._prev_avg_wait = 0.0
        self._prev_avg_tat = 0.0

        self.progress_updated.emit(0)
        self.process_table_updated.emit([])
        self.total_processes_changed.emit(0)
        self.cpu_load_changed.emit(0)
        self.results_updated.emit(0.0, 0.0, 0.0, 0.0)
        self.status_changed.emit("READY")

    # ------------------------------------------------------------------
    # Execution paths
    # ------------------------------------------------------------------
    def _run_static(self) -> None:
        engine = EngineFactory.create(self.algorithm.value)
        result = engine.compute_static(
            self._processes,
            EngineConfig(preemptive=self.preemptive, quantum=self.quantum),
        )

        for item in result.timeline:
            self.gantt_block_added.emit(item.pid, item.start, item.end, item.is_context_switch)

        metrics_by_pid = {m.pid: m for m in result.process_metrics}
        rows = [
            {
                "pid": p.pid,
                "arrival": round(p.arrival_time, 2),
                "burst": round(p.burst_time, 2),
                "remaining": 0.0,
                "priority": p.priority,
                "status": "FINISHED",
                "waiting_time": round(metrics_by_pid[p.pid].waiting_time, 2)
                if p.pid in metrics_by_pid else None,
                "turnaround_time": round(metrics_by_pid[p.pid].turnaround_time, 2)
                if p.pid in metrics_by_pid else None,
            }
            for p in sorted(self._processes, key=lambda x: x.insertion_order)
        ]

        self.process_table_updated.emit(rows)
        self.total_processes_changed.emit(len(rows))
        self.cpu_load_changed.emit(0)
        self.progress_updated.emit(100)

        delta_wait = result.average_wait_time - self._prev_avg_wait
        delta_tat = result.average_turnaround_time - self._prev_avg_tat
        self._prev_avg_wait = result.average_wait_time
        self._prev_avg_tat = result.average_turnaround_time
        self.results_updated.emit(
            result.average_wait_time,
            result.average_turnaround_time,
            delta_wait,
            delta_tat,
        )
        self.status_changed.emit("FINISHED")

    @Slot()
    def _on_live_tick(self) -> None:
        if self._runtime is None:
            self._timer.stop()
            return

        snap = self._runtime.tick()

        if snap.new_slice is not None:
            self.gantt_block_added.emit(
                snap.new_slice.pid,
                snap.new_slice.start,
                snap.new_slice.end,
                snap.new_slice.is_context_switch,
            )

        self.process_table_updated.emit(snap.table_rows)
        self.total_processes_changed.emit(snap.total_processes)
        self.cpu_load_changed.emit(snap.cpu_load)
        self.progress_updated.emit(snap.progress)
        self.results_updated.emit(
            snap.average_wait,
            snap.average_turnaround,
            snap.delta_wait,
            snap.delta_turnaround,
        )

        if snap.completed:
            self._timer.stop()
            self.status_changed.emit("FINISHED")
            self.cpu_load_changed.emit(0)
