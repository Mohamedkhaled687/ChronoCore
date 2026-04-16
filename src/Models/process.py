"""Domain process entities for ChronoCore scheduling backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ProcessStatus(str, Enum):
    """Execution lifecycle states used by table rendering and engines."""

    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    FINISHED = "FINISHED"


@dataclass(slots=True)
class ProcessSpec:
    """Immutable input process definition provided by the UI."""

    pid: str
    arrival_time: float
    burst_time: float
    priority: Optional[int] = None
    insertion_order: int = 0

    def to_dict(self) -> dict:
        return {
            "pid": self.pid,
            "arrival": self.arrival_time,
            "burst": self.burst_time,
            "priority": self.priority,
        }


@dataclass(slots=True)
class ProcessRuntimeState:
    """Mutable runtime state used during simulation."""

    spec: ProcessSpec
    remaining_time: float = field(init=False)
    first_start_time: Optional[float] = None
    completion_time: Optional[float] = None
    status: ProcessStatus = ProcessStatus.READY

    def __post_init__(self) -> None:
        self.remaining_time = self.spec.burst_time

    @property
    def pid(self) -> str:
        return self.spec.pid

    @property
    def arrival_time(self) -> float:
        return self.spec.arrival_time

    @property
    def burst_time(self) -> float:
        return self.spec.burst_time

    @property
    def priority(self) -> Optional[int]:
        return self.spec.priority

    @property
    def is_complete(self) -> bool:
        return self.remaining_time <= 0

    def to_table_row(self, current_time: float = 0.0) -> dict:
        """Serialize to the monitor-table row payload expected by the UI."""
        executed = self.burst_time - max(0.0, self.remaining_time)
        active_end = self.completion_time if self.completion_time is not None else current_time
        turnaround = max(0.0, active_end - self.arrival_time) if self.is_complete else None
        waiting = max(0.0, turnaround - self.burst_time) if turnaround is not None else None
        return {
            "pid": self.pid,
            "arrival": round(self.arrival_time, 2),
            "burst": round(self.burst_time, 2),
            "remaining": max(0.0, round(self.remaining_time, 2)),
            "priority": self.priority,
            "status": self.status.value,
            "waiting_time": round(waiting, 2) if waiting is not None else None,
            "turnaround_time": round(turnaround, 2) if turnaround is not None else None,
        }
