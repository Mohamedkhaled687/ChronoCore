"""Live simulation runtime state machine (1 tick == 1 unit time)."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from src.Models import (
    AlgorithmKey,
    ProcessRuntimeState,
    ProcessSpec,
    ProcessStatus,
    SchedulerSnapshot,
    TimelineSlice,
)


@dataclass(slots=True)
class LiveRuntimeState:
    """Mutable runtime session for live simulation ticks."""

    algorithm: AlgorithmKey
    preemptive: bool = False
    quantum: float = 1.0
    unit_time: float = 1.0
    pending_specs: list[ProcessSpec] = field(default_factory=list)

    current_time: float = 0.0
    running_pid: Optional[str] = None
    rr_quantum_used: float = 0.0
    executed_time: float = 0.0
    last_avg_wait: float = 0.0
    last_avg_tat: float = 0.0

    timeline: list[TimelineSlice] = field(default_factory=list)
    _states: dict[str, ProcessRuntimeState] = field(default_factory=dict)
    _ready_list: list[str] = field(default_factory=list)
    _rr_queue: deque[str] = field(default_factory=deque)

    def __post_init__(self) -> None:
        self.pending_specs.sort(key=lambda s: (s.arrival_time, s.insertion_order))

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def add_process_live(self, spec: ProcessSpec) -> None:
        """Insert a newly arrived process during an ongoing live simulation."""
        self.pending_specs.append(spec)
        self.pending_specs.sort(key=lambda s: (s.arrival_time, s.insertion_order))

    def has_work(self) -> bool:
        if self.pending_specs:
            return True
        if self.running_pid is not None:
            return True
        if self._ready_list or self._rr_queue:
            return True
        return any(not s.is_complete for s in self._states.values())

    # ------------------------------------------------------------------
    # Tick advancement
    # ------------------------------------------------------------------
    def tick(self) -> SchedulerSnapshot:
        self._ingest_arrivals()

        if not self.has_work():
            return self._snapshot(completed=True, new_slice=None, cpu_load=0)

        state = self._get_running_state()
        state = self._select_next_state(state)

        if state is None:
            # Idle tick while waiting for future arrivals
            self.current_time += self.unit_time
            return self._snapshot(completed=False, new_slice=None, cpu_load=0)

        if state.first_start_time is None:
            state.first_start_time = self.current_time
        state.status = ProcessStatus.RUNNING

        run_duration = min(self.unit_time, state.remaining_time)
        if self.algorithm is AlgorithmKey.ROUND_ROBIN:
            run_duration = min(run_duration, self.quantum - self.rr_quantum_used)

        start = self.current_time
        end = start + run_duration

        state.remaining_time -= run_duration
        self.executed_time += run_duration
        self.current_time = end

        new_slice = TimelineSlice(pid=state.pid, start=start, end=end, is_context_switch=False)
        self.timeline.append(new_slice)

        self._ingest_arrivals()
        self._finalize_or_requeue(state, run_duration)

        completed = not self.has_work()
        return self._snapshot(completed=completed, new_slice=new_slice, cpu_load=100)

    # ------------------------------------------------------------------
    # Internal scheduling behavior
    # ------------------------------------------------------------------
    def _ingest_arrivals(self) -> None:
        while self.pending_specs and self.pending_specs[0].arrival_time <= self.current_time:
            spec = self.pending_specs.pop(0)
            runtime = ProcessRuntimeState(spec=spec)
            runtime.status = ProcessStatus.READY
            self._states[spec.pid] = runtime
            if self.algorithm is AlgorithmKey.ROUND_ROBIN:
                self._rr_queue.append(spec.pid)
            else:
                self._ready_list.append(spec.pid)

    def _get_running_state(self) -> Optional[ProcessRuntimeState]:
        if self.running_pid is None:
            return None
        state = self._states.get(self.running_pid)
        if state is None or state.is_complete:
            self.running_pid = None
            return None
        return state

    def _select_next_state(self, current: Optional[ProcessRuntimeState]) -> Optional[ProcessRuntimeState]:
        if self.algorithm is AlgorithmKey.ROUND_ROBIN:
            return self._select_rr(current)

        candidates = [self._states[pid] for pid in self._ready_list if not self._states[pid].is_complete]
        if current and not current.is_complete:
            if self.algorithm in (AlgorithmKey.FCFS,) or (
                self.algorithm in (AlgorithmKey.SJF, AlgorithmKey.PRIORITY) and not self.preemptive
            ):
                return current
            candidates.append(current)

        if not candidates:
            self.running_pid = None
            return None

        candidates.sort(key=self._candidate_sort_key)
        selected = candidates[0]
        self.running_pid = selected.pid
        if selected.pid in self._ready_list:
            self._ready_list.remove(selected.pid)

        if current and current is not selected and not current.is_complete:
            if current.pid not in self._ready_list:
                self._ready_list.append(current.pid)
            current.status = ProcessStatus.WAITING

        for pid in self._ready_list:
            if not self._states[pid].is_complete:
                self._states[pid].status = ProcessStatus.WAITING
        return selected

    def _select_rr(self, current: Optional[ProcessRuntimeState]) -> Optional[ProcessRuntimeState]:
        if current and not current.is_complete and self.rr_quantum_used < self.quantum:
            return current

        if self._rr_queue:
            pid = self._rr_queue.popleft()
            while pid in self._states and self._states[pid].is_complete and self._rr_queue:
                pid = self._rr_queue.popleft()
            state = self._states.get(pid)
            if state and not state.is_complete:
                self.running_pid = pid
                self.rr_quantum_used = 0.0
                for qpid in self._rr_queue:
                    if not self._states[qpid].is_complete:
                        self._states[qpid].status = ProcessStatus.WAITING
                return state

        self.running_pid = None
        self.rr_quantum_used = 0.0
        return None

    def _candidate_sort_key(self, state: ProcessRuntimeState) -> tuple:
        if self.algorithm is AlgorithmKey.FCFS:
            return (state.arrival_time, state.spec.insertion_order)
        if self.algorithm is AlgorithmKey.SJF:
            metric = state.remaining_time if self.preemptive else state.burst_time
            return (metric, state.arrival_time, state.spec.insertion_order)
        if self.algorithm is AlgorithmKey.PRIORITY:
            priority = state.priority if state.priority is not None else 10**9
            if self.preemptive:
                return (priority, state.arrival_time, state.spec.insertion_order)
            return (priority, state.arrival_time, state.spec.insertion_order)
        return (state.arrival_time, state.spec.insertion_order)

    def _finalize_or_requeue(self, state: ProcessRuntimeState, consumed: float) -> None:
        if self.algorithm is AlgorithmKey.ROUND_ROBIN:
            self.rr_quantum_used += consumed

        if state.remaining_time <= 1e-9:
            state.remaining_time = 0.0
            state.completion_time = self.current_time
            state.status = ProcessStatus.FINISHED
            self.running_pid = None
            self.rr_quantum_used = 0.0
            return

        if self.algorithm is AlgorithmKey.ROUND_ROBIN and self.rr_quantum_used >= self.quantum:
            state.status = ProcessStatus.WAITING
            self._rr_queue.append(state.pid)
            self.running_pid = None
            self.rr_quantum_used = 0.0
            return

        # Still running into next tick for non-preemptive or unfinished quantum.
        state.status = ProcessStatus.RUNNING

    # ------------------------------------------------------------------
    # Snapshot / metrics
    # ------------------------------------------------------------------
    def _snapshot(self, completed: bool, new_slice: Optional[TimelineSlice], cpu_load: int) -> SchedulerSnapshot:
        avg_wait, avg_tat = self._calculate_running_averages()
        delta_wait = avg_wait - self.last_avg_wait
        delta_tat = avg_tat - self.last_avg_tat
        self.last_avg_wait = avg_wait
        self.last_avg_tat = avg_tat

        total_burst = sum(s.burst_time for s in self._states.values()) + sum(
            spec.burst_time for spec in self.pending_specs
        )
        progress = int((self.executed_time / total_burst) * 100) if total_burst > 0 else 0
        progress = max(0, min(100, progress))
        if completed:
            progress = 100

        rows = [
            state.to_table_row(current_time=self.current_time)
            for state in sorted(self._states.values(), key=lambda s: s.spec.insertion_order)
        ]

        return SchedulerSnapshot(
            current_time=round(self.current_time, 4),
            running_pid=self.running_pid,
            table_rows=rows,
            cpu_load=cpu_load,
            total_processes=len(rows),
            progress=progress,
            new_slice=new_slice,
            completed=completed,
            average_wait=round(avg_wait, 4),
            average_turnaround=round(avg_tat, 4),
            delta_wait=round(delta_wait, 4),
            delta_turnaround=round(delta_tat, 4),
        )

    def _calculate_running_averages(self) -> tuple[float, float]:
        if not self._states:
            return 0.0, 0.0

        wait_total = 0.0
        tat_total = 0.0
        n = len(self._states)
        for state in self._states.values():
            executed = state.burst_time - state.remaining_time
            active_time = (
                state.completion_time if state.completion_time is not None else self.current_time
            )
            tat = max(0.0, active_time - state.arrival_time)
            wait = max(0.0, tat - executed)
            wait_total += wait
            tat_total += tat

        return wait_total / n, tat_total / n
