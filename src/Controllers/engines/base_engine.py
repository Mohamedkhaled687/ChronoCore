"""Base contract and shared helpers for scheduler engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Optional

from src.Models import ProcessSpec, ProcessRuntimeState, ProcessMetrics, ScheduleResult, TimelineSlice


@dataclass(slots=True)
class EngineConfig:
    preemptive: bool = False
    quantum: Optional[float] = None


class BaseSchedulerEngine(ABC):
    """Abstract scheduling engine interface."""

    @abstractmethod
    def compute_static(self, processes: list[ProcessSpec], config: EngineConfig) -> ScheduleResult:
        """Return a complete static schedule result."""

    def step(self, state, incoming_processes):
        """Reserved for future per-tick engine stepping."""
        raise NotImplementedError("Per-step mode is orchestrated by live runtime")

    @staticmethod
    def build_runtime_states(processes: Iterable[ProcessSpec]) -> list[ProcessRuntimeState]:
        return [ProcessRuntimeState(spec=p) for p in processes]

    @staticmethod
    def append_slice(timeline: list[TimelineSlice], pid: str, start: float, end: float) -> None:
        if end <= start:
            return
        if timeline and timeline[-1].pid == pid and not timeline[-1].is_context_switch:
            timeline[-1].end = end
            return
        timeline.append(TimelineSlice(pid=pid, start=start, end=end, is_context_switch=False))

    @staticmethod
    def finalize_result(states: list[ProcessRuntimeState], timeline: list[TimelineSlice]) -> ScheduleResult:
        metrics: list[ProcessMetrics] = []
        for state in sorted(states, key=lambda s: s.spec.insertion_order):
            completion = state.completion_time if state.completion_time is not None else state.arrival_time
            turnaround = completion - state.arrival_time
            waiting = turnaround - state.burst_time
            response = (state.first_start_time or state.arrival_time) - state.arrival_time
            metrics.append(
                ProcessMetrics(
                    pid=state.pid,
                    waiting_time=round(waiting, 4),
                    turnaround_time=round(turnaround, 4),
                    response_time=round(response, 4),
                )
            )

        avg_wait = round(sum(m.waiting_time for m in metrics) / len(metrics), 4) if metrics else 0.0
        avg_tat = (
            round(sum(m.turnaround_time for m in metrics) / len(metrics), 4) if metrics else 0.0
        )
        return ScheduleResult(
            timeline=timeline,
            process_metrics=metrics,
            average_wait_time=avg_wait,
            average_turnaround_time=avg_tat,
        )
