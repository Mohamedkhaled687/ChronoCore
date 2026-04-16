"""Priority scheduling engine with FCFS tie-break support."""

from __future__ import annotations

from src.Controllers.engines.base_engine import BaseSchedulerEngine, EngineConfig
from src.Models import ProcessSpec, ProcessStatus, ScheduleResult


class PriorityEngine(BaseSchedulerEngine):
    def compute_static(self, processes: list[ProcessSpec], config: EngineConfig) -> ScheduleResult:
        if config.preemptive:
            return self._compute_preemptive(processes)
        return self._compute_non_preemptive(processes)

    @staticmethod
    def _priority_key(state) -> tuple:
        # smaller priority number = higher priority. FCFS tie-break.
        pr = state.priority if state.priority is not None else 10**9
        return (pr, state.arrival_time, state.spec.insertion_order)

    def _compute_non_preemptive(self, processes: list[ProcessSpec]) -> ScheduleResult:
        timeline = []
        states = self.build_runtime_states(processes)
        pending = sorted(states, key=lambda s: (s.arrival_time, s.spec.insertion_order))
        ready = []
        time = 0.0

        while pending or ready:
            while pending and pending[0].arrival_time <= time:
                ready.append(pending.pop(0))

            if not ready:
                time = pending[0].arrival_time
                continue

            ready.sort(key=self._priority_key)
            current = ready.pop(0)
            if current.first_start_time is None:
                current.first_start_time = time
            current.status = ProcessStatus.RUNNING
            start = time
            end = start + current.remaining_time
            current.remaining_time = 0.0
            current.completion_time = end
            current.status = ProcessStatus.FINISHED
            self.append_slice(timeline, current.pid, start, end)
            time = end

            for item in ready:
                if item.status != ProcessStatus.FINISHED:
                    item.status = ProcessStatus.WAITING

        return self.finalize_result(states, timeline)

    def _compute_preemptive(self, processes: list[ProcessSpec]) -> ScheduleResult:
        timeline = []
        states = self.build_runtime_states(processes)
        pending = sorted(states, key=lambda s: (s.arrival_time, s.spec.insertion_order))
        ready = []
        time = 0.0

        while pending or ready:
            while pending and pending[0].arrival_time <= time:
                ready.append(pending.pop(0))

            ready = [s for s in ready if not s.is_complete]
            if not ready:
                if pending:
                    time = pending[0].arrival_time
                    continue
                break

            ready.sort(key=self._priority_key)
            current = ready[0]
            if current.first_start_time is None:
                current.first_start_time = time
            current.status = ProcessStatus.RUNNING

            next_arrival = pending[0].arrival_time if pending else None
            run_until = time + current.remaining_time
            if next_arrival is not None and next_arrival < run_until:
                run_until = next_arrival

            duration = run_until - time
            current.remaining_time -= duration
            self.append_slice(timeline, current.pid, time, run_until)
            time = run_until

            if current.remaining_time <= 1e-9:
                current.remaining_time = 0.0
                current.completion_time = time
                current.status = ProcessStatus.FINISHED
                ready = [s for s in ready if s is not current]

            for item in ready:
                if item is not current and item.status != ProcessStatus.FINISHED:
                    item.status = ProcessStatus.WAITING

        return self.finalize_result(states, timeline)
