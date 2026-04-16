"""Shared scheduling types and result containers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AlgorithmKey(str, Enum):
    FCFS = "fcfs"
    SJF = "sjf"
    PRIORITY = "priority"
    ROUND_ROBIN = "round_robin"


class SimulationMode(str, Enum):
    STATIC = "static"
    LIVE = "live"


@dataclass(slots=True)
class TimelineSlice:
    """Represents one contiguous gantt segment."""

    pid: str
    start: float
    end: float
    is_context_switch: bool = False

    def to_dict(self) -> dict:
        return {
            "pid": self.pid,
            "start": self.start,
            "end": self.end,
            "is_context_switch": self.is_context_switch,
        }


@dataclass(slots=True)
class ProcessMetrics:
    pid: str
    waiting_time: float
    turnaround_time: float
    response_time: float

    def to_dict(self) -> dict:
        return {
            "pid": self.pid,
            "waiting_time": self.waiting_time,
            "turnaround_time": self.turnaround_time,
            "response_time": self.response_time,
        }


@dataclass(slots=True)
class ScheduleResult:
    timeline: list[TimelineSlice]
    process_metrics: list[ProcessMetrics]
    average_wait_time: float
    average_turnaround_time: float

    def timeline_payload(self) -> list[dict]:
        return [item.to_dict() for item in self.timeline]


@dataclass(slots=True)
class SchedulerSnapshot:
    """One live-tick snapshot for UI updates."""

    current_time: float
    running_pid: Optional[str]
    table_rows: list[dict]
    cpu_load: int
    total_processes: int
    progress: int
    new_slice: Optional[TimelineSlice] = None
    completed: bool = False
    average_wait: float = 0.0
    average_turnaround: float = 0.0
    delta_wait: float = 0.0
    delta_turnaround: float = 0.0
