"""Round Robin scheduling engine."""

from __future__ import annotations

from collections import deque

from src.Controllers.engines.base_engine import BaseSchedulerEngine, EngineConfig
from src.Models import ProcessSpec, ProcessStatus, ScheduleResult


class RoundRobinEngine(BaseSchedulerEngine):
    def compute_static(self, processes: list[ProcessSpec], config: EngineConfig) -> ScheduleResult:
        quantum = config.quantum or 1.0
        if quantum <= 0:
            raise ValueError("Round Robin quantum must be positive")

        timeline = []
        states = self.build_runtime_states(processes)
        pending = sorted(states, key=lambda s: (s.arrival_time, s.spec.insertion_order))
        ready = deque()
        time = 0.0

        while pending or ready:
            while pending and pending[0].arrival_time <= time:
                ready.append(pending.pop(0))

            if not ready:
                time = pending[0].arrival_time
                continue

            current = ready.popleft()
            if current.first_start_time is None:
                current.first_start_time = time
            current.status = ProcessStatus.RUNNING

            run_duration = min(quantum, current.remaining_time)
            start = time
            end = time + run_duration
            current.remaining_time -= run_duration
            self.append_slice(timeline, current.pid, start, end)
            time = end

            while pending and pending[0].arrival_time <= time:
                ready.append(pending.pop(0))

            if current.remaining_time <= 1e-9:
                current.remaining_time = 0.0
                current.completion_time = time
                current.status = ProcessStatus.FINISHED
            else:
                current.status = ProcessStatus.WAITING
                ready.append(current)

            for item in ready:
                if item.status != ProcessStatus.FINISHED:
                    item.status = ProcessStatus.WAITING

        return self.finalize_result(states, timeline)
