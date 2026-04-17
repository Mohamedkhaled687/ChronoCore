"""First-Come First-Served scheduling engine."""

from __future__ import annotations

from src.Controllers.engines.base_engine import BaseSchedulerEngine, EngineConfig
from src.Models import ProcessSpec, ProcessStatus, ScheduleResult


class FCFSEngine(BaseSchedulerEngine):
    def compute_static(self, processes: list[ProcessSpec], config: EngineConfig) -> ScheduleResult:
        timeline = []
        states = self.build_runtime_states(sorted(processes, key=lambda p: (p.arrival_time, p.insertion_order)))

        time = 0.0
        for state in states:
            if time < state.arrival_time:
                time = state.arrival_time
            state.status = ProcessStatus.RUNNING
            state.first_start_time = time
            start = time
            end = start + state.remaining_time
            state.remaining_time = 0.0
            state.completion_time = end
            state.status = ProcessStatus.FINISHED
            self.append_slice(timeline, state.pid, start, end)
            time = end

        return self.finalize_result(states, timeline)
