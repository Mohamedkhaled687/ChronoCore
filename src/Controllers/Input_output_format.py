from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

@dataclass
class Process:
    pid: str
    arrival: float
    burst: float
    priority: int = 0
    remaining: float = field(init=False)

    def __post_init__(self) -> None:
        self.remaining = self.burst

    @classmethod
    def from_dict(cls, d: dict) -> "Process":
        """
        Build a Process from the dict emitted by InputPanelWidget.process_added.

        Expected keys: pid, arrival, burst
        Optional keys: priority (int | None), queue_level (int | None)
        Ignored keys:  quantum  (consumed by run_algorithm, not stored per-process)
        """
        return cls(
            pid=str(d["pid"]),
            arrival=float(d["arrival"]),
            burst=float(d["burst"]),
            priority=int(d["priority"]) if d.get("priority") is not None else 0,
        )


@dataclass
class GanttEntry:
    pid: str
    start: float
    end: float
    is_context_switch: bool = False   # True when two consecutive blocks differ in pid

    def to_ui_dict(self) -> dict:
        """
        Returns a dict ready to unpack into GanttChartWidget.add_gantt_block(**block).

        Signature:  add_gantt_block(pid, start, end, is_context_switch=False)
        """
        return {
            "pid": self.pid,
            "start": self.start,
            "end": self.end,
            "is_context_switch": self.is_context_switch,
        }


@dataclass
class ProcessResult:
    pid: str
    arrival: float
    burst: float
    priority: int
    completion: float
    waiting_time: float
    turnaround_time: float
    remaining: float = 0.0      # 0 once scheduling is complete (static mode)
    status: str = "FINISHED"    # "FINISHED" | "RUNNING" | "WAITING"

    def to_ui_dict(self) -> dict:
        """
        Returns a dict ready for a row in ActiveStateMonitorWidget.update_process_table().

        Expected keys: pid, arrival, burst, remaining, priority, status
        """
        return {
            "pid": self.pid,
            "arrival": self.arrival,
            "burst": self.burst,
            "remaining": self.remaining,
            "priority": self.priority,
            "status": self.status,
        }


@dataclass
class ScheduleResult:
    gantt: List[GanttEntry]
    processes: List[ProcessResult]
    avg_waiting_time: float
    avg_turnaround_time: float

    def to_gantt_list(self) -> list[dict]:
        """
        Returns a list of dicts for GanttChartWidget.add_gantt_block(**block).

        Context-switch markers are auto-inserted between blocks that belong
        to different processes, giving the chart the coloured separator blocks.
        """
        blocks: list[dict] = []
        for i, entry in enumerate(self.gantt):
            blocks.append(entry.to_ui_dict())
            # Insert a thin context-switch block between two different pids
            if i + 1 < len(self.gantt) and self.gantt[i + 1].pid != entry.pid:
                blocks.append({
                    "pid": "CS",
                    "start": entry.end,
                    "end": entry.end,           # zero-width — chart renders it visually
                    "is_context_switch": True,
                })
        return blocks

    def to_process_table(self) -> list[dict]:
        """
        Returns a list of row dicts for ActiveStateMonitorWidget.update_process_table().
        """
        return [p.to_ui_dict() for p in self.processes]

def _make_results(
    procs: List[Process],
    completion: Dict[str, float],
) -> Tuple[List[ProcessResult], float, float]:
    results: List[ProcessResult] = []
    for p in procs:
        comp = completion[p.pid]
        tat = comp - p.arrival
        wt = tat - p.burst
        results.append(ProcessResult(
            pid=p.pid,
            arrival=p.arrival,
            burst=p.burst,
            priority=p.priority,
            completion=comp,
            waiting_time=round(wt, 4),
            turnaround_time=round(tat, 4),
            remaining=0.0,
            status="FINISHED",
        ))
    avg_wt = sum(r.waiting_time for r in results) / len(results)
    avg_tat = sum(r.turnaround_time for r in results) / len(results)
    return results, round(avg_wt, 4), round(avg_tat, 4)