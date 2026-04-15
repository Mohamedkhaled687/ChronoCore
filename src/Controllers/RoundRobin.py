"""
Round Robin CPU Scheduling Algorithm

Public API:
RoundRobinScheduler(quantum)
    add_process(process)   – register a Process (safe to call mid-run).
    tick()                 – advance the clock by 1 unit; returns a LiveSnapshot.
    simulate_all()         – run to completion; returns a ScheduleResult.
    all_done()             – True when every registered process has finished.

LiveSnapshot dict  (returned by tick())
{
    "time"               : float,         # clock value after this tick
    "gantt"              : list[GanttEntry],   # full Gantt log so far
    "gantt_blocks"       : list[dict],    # ready for GanttChartWidget  (via to_gantt_list)
    "process_table"      : list[dict],    # ready for ActiveStateMonitorWidget
    "ready_q"            : list[str],     # pids currently in ready queue
    "running"            : str | None,    # pid on CPU, or None
    "avg_waiting_time"   : float,         # average over *finished* processes only
    "avg_turnaround_time": float,         # average over *finished* processes only
}

ScheduleResult (returned by simulate_all())
A fully populated ScheduleResult dataclass from Input_output_format.py.
Call  result.to_gantt_list()       → list[dict] for GanttChartWidget
      result.to_process_table()    → list[dict] for ActiveStateMonitorWidget

Usage example:
    from Input_output_format import Process
    from RoundRobin import RoundRobinScheduler

    # Build processes from raw dicts (as emitted by InputPanelWidget)
    p1 = Process.from_dict({"pid": "P1", "arrival": 0, "burst": 10})
    p2 = Process.from_dict({"pid": "P2", "arrival": 0, "burst": 6})
    p3 = Process.from_dict({"pid": "P3", "arrival": 5, "burst": 4})

    # ── Option A : instant simulation ────────────────────────────────────────
    scheduler = RoundRobinScheduler(quantum=3)
    scheduler.add_process(p1)
    scheduler.add_process(p2)
    scheduler.add_process(p3)

    result = scheduler.simulate_all()          # returns ScheduleResult
    for row in result.to_process_table():
        print(row["pid"], row["status"])
    for block in result.to_gantt_list():
        print(block)
    print("Avg WT :", result.avg_waiting_time)
    print("Avg TAT:", result.avg_turnaround_time)

    # ── Option B : tick-by-tick live mode (driven by a GUI timer) ────────────
    scheduler2 = RoundRobinScheduler(quantum=3)
    scheduler2.add_process(Process.from_dict({"pid": "P1", "arrival": 0, "burst": 10}))

    while not scheduler2.all_done():
        snap = scheduler2.tick()               # returns LiveSnapshot dict
        print(snap["time"], snap["running"], snap["ready_q"])
        # pass to GUI:
        # gantt_widget.update(snap["gantt_blocks"])
        # table_widget.update(snap["process_table"])
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Dict, List, Optional

# Import all shared types from the project's format contract.
from Input_output_format import (
    GanttEntry,
    Process,
    ProcessResult,
    ScheduleResult,
    _make_results,
)


#  RoundRobinScheduler

class RoundRobinScheduler:
    """
    Parameters:
    quantum : float
        Time quantum (> 0).  A running process is preempted once it has
        used `quantum` consecutive CPU units without finishing.

    Attributes (read-only externally)
    quantum       : float   Time quantum for this scheduler instance.
    current_time  : float   Monotonically increasing logical clock.
    processes     : list    Every Process ever registered (insertion order).
    gantt         : list    Accumulated log as GanttEntry objects.
    ready_queue   : deque   Processes waiting for CPU in FIFO order.
    """

    def __init__(self, quantum: float) -> None:
        #configuration
        self.quantum: float = quantum

        # clock & state
        self.current_time: float         = 0
        self.processes:    List[Process] = []
        self.ready_queue:  deque         = deque()
        self.gantt:        List[GanttEntry] = []

        # private bookkeeping
        self._lock             = threading.Lock()
        self._current_proc:    Optional[Process] = None
        self._time_in_quantum: float = 0

        # pids that have already entered the ready queue (prevents double-admission)
        self._admitted_pids: set = set()

        # per-process runtime metadata not stored on the Process dataclass itself:
        # { pid: {"start_time": float | None, "finish_time": float | None} }
        self._proc_meta: Dict[str, dict] = {}

        # ordered list of processes that have completed (used by _make_results)
        self._finished_procs: List[Process] = []

        # completion-time map required by _make_results helper
        self._completion: Dict[str, float] = {}

    #  Public API

    def add_process(self, process: Process) -> None:
        """
        Register a new process with the scheduler.

        Parameters
        ----------
        process : Process
            A Process instance from Input_output_format.  Its `arrival` field
            determines when it first becomes eligible for the CPU.
            Accepted as-is; `process.remaining` must equal `process.burst`
            (i.e. the process must not have been run by another scheduler).
        """
        with self._lock:
            self.processes.append(process)
            # initialise per-process metadata slot
            self._proc_meta[process.pid] = {
                "start_time" : None,   # first tick on CPU
                "finish_time": None,   # tick immediately after completion
            }

    def tick(self) -> dict:
        """
        Advance the simulation clock by one time unit and return a LiveSnapshot.

        Each call performs the following steps in order:

        1. Admit — any process whose arrival <= current_time and that has
           not yet been queued is appended to the ready queue.
        2. Dispatch — if the CPU is free, dequeue the next process from
           the head of the ready queue.
        3. Execute — decrement the running process's `remaining` by 1 and
           extend (or open) its GanttEntry.
        4. *Finish — if remaining == 0 the process is marked done, its
           finish_time / completion are recorded, and it leaves the CPU.
        5. Preempt — else if the process has used a full quantum, admit
           any newly arrived processes first, then push the preempted process
           to the back of the ready queue.
        6. Idle — if no process is available, record / extend an IDLE
           GanttEntry.
        7. Increment current_time and return a LiveSnapshot dict.

        Returns
        dict  (LiveSnapshot)
        """
        with self._lock:
            t = self.current_time

            # Step 1 : admit newly arrived processes
            for p in self.processes:
                if (p.arrival <= t
                        and p.pid not in self._admitted_pids
                        and p.remaining > 0):
                    self.ready_queue.append(p)
                    self._admitted_pids.add(p.pid)

            # Step 2 : dispatch if CPU is free
            if self._current_proc is None or self._current_proc.remaining <= 0:
                # release a just-finished process from the CPU slot
                if self._current_proc and self._current_proc.remaining <= 0:
                    self._current_proc = None

                if self.ready_queue:
                    self._current_proc    = self.ready_queue.popleft()
                    self._time_in_quantum = 0   # fresh quantum counter

            # Step 3 : execute one unit
            if self._current_proc:
                p    = self._current_proc
                meta = self._proc_meta[p.pid]

                # record first-time-on-CPU
                if meta["start_time"] is None:
                    meta["start_time"] = t

                # consume one unit of burst
                p.remaining           -= 1
                self._time_in_quantum += 1

                # update Gantt: extend the last GanttEntry if it belongs to the
                # same process and its end aligns with the current tick,
                # otherwise open a fresh GanttEntry.
                if (self.gantt
                        and self.gantt[-1].pid == p.pid
                        and self.gantt[-1].end == t):
                    self.gantt[-1].end = t + 1
                else:
                    self.gantt.append(GanttEntry(pid=p.pid, start=t, end=t + 1))

                # Step 4 : check for process completion
                if p.remaining <= 0:
                    meta["finish_time"]       = t + 1
                    self._completion[p.pid]   = t + 1
                    self._finished_procs.append(p)
                    self._current_proc = None

                # Step 5 : preempt when quantum is exhausted
                elif self._time_in_quantum >= self.quantum:
                    # admit processes that arrived during this quantum BEFORE
                    # re-queueing the preempted one — preserves arrival order.
                    for new_p in self.processes:
                        if (new_p.arrival <= t + 1
                                and new_p.pid not in self._admitted_pids
                                and new_p.remaining > 0):
                            self.ready_queue.append(new_p)
                            self._admitted_pids.add(new_p.pid)

                    # send the preempted process to the back of the queue
                    self.ready_queue.append(p)
                    self._current_proc    = None
                    self._time_in_quantum = 0

            else:
                #  Step 6 : CPU idle — no runnable process
                # Merge consecutive idle ticks into one GanttEntry.
                if (self.gantt
                        and self.gantt[-1].pid == "IDLE"
                        and self.gantt[-1].end == t):
                    self.gantt[-1].end = t + 1
                else:
                    self.gantt.append(GanttEntry(pid="IDLE", start=t, end=t + 1))

            # Step 7 : advance clock and return snapshot
            self.current_time += 1
            return self._live_snapshot()

    def simulate_all(self) -> ScheduleResult:
        """
        Run the simulation to completion without live timing.

        Repeatedly calls tick() until every registered process has finished
        and both the ready queue and the CPU are empty.

        Returns
        -------
        ScheduleResult
            Fully populated result object from Input_output_format.
            Use  result.to_gantt_list()     -> blocks for GanttChartWidget
                 result.to_process_table()  -> rows  for ActiveStateMonitorWidget

        """
        while True:
            if (self.all_done()
                    and not self.ready_queue
                    and self._current_proc is None):
                break
            self.tick()
            if self.current_time > 10_000:   # safety guard
                break

        return self._build_schedule_result()

    def all_done(self) -> bool:
        """
        Return True when every registered process has finished.

        Returns False if no processes have been registered yet.
        """
        with self._lock:
            procs = list(self.processes)
        return bool(procs) and all(p.remaining <= 0 for p in procs)

    #  Private helpers
    def _live_snapshot(self) -> dict:
        """
        Build a LiveSnapshot dict from the current scheduler state.

        Called at the end of tick() while the lock is still held.
        Produces both raw GanttEntry objects and UI-ready dicts so the caller
        can choose whichever form suits the widget being updated.

        Returns
        -------
        dict — see module docstring for full key list.
        """
        running_pid = self._current_proc.pid if self._current_proc else None

        # build ProcessResult for every known process
        process_table: List[dict] = []
        for p in self.processes:
            if p.remaining <= 0:
                # process is finished — use accurate computed values
                comp = self._completion[p.pid]
                tat  = comp - p.arrival
                wt   = tat  - p.burst
                pr   = ProcessResult(
                    pid             = p.pid,
                    arrival         = p.arrival,
                    burst           = p.burst,
                    priority        = p.priority,
                    completion      = comp,
                    waiting_time    = round(wt,  4),
                    turnaround_time = round(tat, 4),
                    remaining       = 0.0,
                    status          = "FINISHED",
                )
            else:
                # process is still alive — no final stats available yet
                pr = ProcessResult(
                    pid             = p.pid,
                    arrival         = p.arrival,
                    burst           = p.burst,
                    priority        = p.priority,
                    completion      = 0.0,      # not yet known
                    waiting_time    = 0.0,      # not yet known
                    turnaround_time = 0.0,      # not yet known
                    remaining       = p.remaining,
                    status          = "RUNNING" if p.pid == running_pid else "WAITING",
                )

            process_table.append(pr.to_ui_dict())

        #  compute running averages over finished processes only
        finished = [p for p in self.processes if p.remaining <= 0]
        if finished:
            avg_wt  = sum(
                self._completion[p.pid] - p.arrival - p.burst for p in finished
            ) / len(finished)
            avg_tat = sum(
                self._completion[p.pid] - p.arrival for p in finished
            ) / len(finished)
        else:
            avg_wt = avg_tat = 0.0

        #wrap gantt in a temporary ScheduleResult to reuse to_gantt_list()
        temp_result = ScheduleResult(
            gantt               = list(self.gantt),
            processes           = [],
            avg_waiting_time    = round(avg_wt,  4),
            avg_turnaround_time = round(avg_tat, 4),
        )

        return {
            "time"               : self.current_time,
            "gantt"              : list(self.gantt),           # raw GanttEntry objects
            "gantt_blocks"       : temp_result.to_gantt_list(), # UI-ready dicts
            "process_table"      : process_table,              # UI-ready dicts
            "ready_q"            : [p.pid for p in list(self.ready_queue)],
            "running"            : running_pid,
            "avg_waiting_time"   : round(avg_wt,  4),
            "avg_turnaround_time": round(avg_tat, 4),
        }

    def _build_schedule_result(self) -> ScheduleResult:
        """
        Construct a final ScheduleResult after all processes have finished.

        Uses _make_results() from Input_output_format to compute waiting times
        and turnaround times, then wraps everything in a ScheduleResult.

        Called exclusively by simulate_all().

        Returns
        -------
        ScheduleResult
            Contains the final Gantt log, per-process results, and averages.
        """
        # _make_results expects the original Process list and a completion map
        proc_results, avg_wt, avg_tat = _make_results(
            self.processes,
            self._completion,
        )

        return ScheduleResult(
            gantt               = list(self.gantt),
            processes           = proc_results,
            avg_waiting_time    = avg_wt,
            avg_turnaround_time = avg_tat,
        )

    def __repr__(self) -> str:
        return (
            f"RoundRobinScheduler(quantum={self.quantum}, "
            f"time={self.current_time}, "
            f"processes={len(self.processes)})"
        )