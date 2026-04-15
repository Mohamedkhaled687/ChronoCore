"""
RoundRobin.py
===============
Complexity
----------
- Time  : O(n) per tick, where n = number of processes ever added.
- Space : O(n) for process list + O(n) for ready-queue entries.

Public API
----------
Process(pid, arrival, burst)
    Immutable identity; mutable runtime state (remaining, finish_time, …).

RoundRobinScheduler(quantum)
    add_process(process)   – register a new Process (safe to call mid-run).
    tick()                 – advance the clock by 1 unit; returns a snapshot.
    simulate_all()         – run to completion; returns final snapshot.
    all_done()             – True when every registered process has finished.

Snapshot dict (returned by tick / simulate_all)
------------------------------------------------
{
    "time"    : int,          # current clock value after this tick
    "gantt"   : list of (pid, start, end),  # full Gantt log so far
    "procs"   : list of process-snapshot dicts (see _proc_snap),
    "ready_q" : list of pid strings currently in the ready queue,
    "running" : str | None,   # pid of the process on CPU, or None
}

Usage example
-------------
    from RoundRobin import Process, RoundRobinScheduler

    scheduler = RoundRobinScheduler(quantum=3)
    scheduler.add_process(Process("P1", arrival=0, burst=10))
    scheduler.add_process(Process("P2", arrival=0, burst=6))
    scheduler.add_process(Process("P3", arrival=5, burst=4))

    # Option A – instant simulation
    final = scheduler.simulate_all()
    for p in final["procs"]:
        print(f"{p['pid']}  WT={p['wt']}  TAT={p['tat']}")

    # Option B – tick-by-tick (e.g. driven by a GUI timer at 1 tick / second)
    scheduler2 = RoundRobinScheduler(quantum=3)
    scheduler2.add_process(Process("P1", 0, 10))
    while not scheduler2.all_done():
        snap = scheduler2.tick()
        print(snap["time"], snap["running"], snap["ready_q"])
"""

import threading
from collections import deque


#  Process

class Process:
    """
    Represents a single process in the scheduling simulation.

    Parameters
    ----------
    pid : str
        Unique process identifier (e.g. "P1", "P2").
    arrival : int
        The time unit at which this process enters the system (≥ 0).
    burst : int
        Total CPU time required by the process (> 0).

    Runtime attributes (managed by the scheduler)
    -----------------------------------------------
    remaining : int
        CPU time still needed; decremented by 1 each tick the process runs.
        Starts equal to `burst`; reaches 0 when the process finishes.
    start_time : int | None
        Clock value when the process first gets the CPU.  None until set.
    finish_time : int | None
        Clock value immediately after the process completes.  None until set.
    waiting_time : int
        Total time spent waiting in the ready queue.
        Computed as  turnaround − burst  once the process finishes.
    turnaround : int
        Total elapsed time from arrival to completion.
        Computed as  finish_time − arrival  once the process finishes.
    """

    def __init__(self, pid: str, arrival: int, burst: int) -> None:
        # ── identity ──────────────────────────────────────────────────────────
        self.pid      = pid
        self.arrival  = arrival
        self.burst    = burst       # original (never changes after creation)

        # ── mutable runtime state ─────────────────────────────────────────────
        self.remaining    = burst   # counts down to 0
        self.start_time   = None    # set on first CPU allocation
        self.finish_time  = None    # set when remaining reaches 0
        self.waiting_time = 0       # calculated at finish
        self.turnaround   = 0       # calculated at finish

    # ── helpers ───────────────────────────────────────────────────────────────

    def is_done(self) -> bool:
        """Return True when the process has consumed all its burst time."""
        return self.remaining <= 0

    def __repr__(self) -> str:
        return (
            f"Process(pid={self.pid!r}, arrival={self.arrival}, "
            f"burst={self.burst}, remaining={self.remaining})"
        )


#  RoundRobinScheduler

class RoundRobinScheduler:
    """
    Round Robin CPU scheduler — pure logic.

    The scheduler operates on a discrete time axis.  Each call to tick()
    advances the clock by exactly one unit and returns a snapshot of the
    full scheduler state at that moment.

    Parameters
    ----------
    quantum : int
        Time quantum (> 0).  A running process is preempted once it has
        used `quantum` consecutive CPU units without finishing.

    Attributes (read-only externally)
    -----------------------------------
    quantum : int       Time quantum for this scheduler instance.
    current_time : int  Monotonically increasing logical clock.
    processes : list    Every Process ever registered (in insertion order).
    gantt : list        Accumulated Gantt log as (pid, start, end) tuples.
    ready_queue : deque Processes waiting for CPU in FIFO order.
    """

    def __init__(self, quantum: int) -> None:
        # ── configuration ─────────────────────────────────────────────────────
        self.quantum = quantum

        # ── clock & state ─────────────────────────────────────────────────────
        self.current_time     = 0
        self.processes        = []          # all registered processes
        self.ready_queue      = deque()     # FIFO queue of ready processes
        self.gantt            = []          # (pid, start, end) log

        # ── private bookkeeping ───────────────────────────────────────────────
        self._lock            = threading.Lock()
        self._current_proc    = None        # process currently on the CPU
        self._time_in_quantum = 0           # ticks used in the current quantum
        self._finished        = []          # completed processes (in order)
        self._admitted_pids   = set()       # pids already placed in ready queue

    #  Public API

    def add_process(self, process: Process) -> None:
        """
        Register a new process with the scheduler.

        Parameters
        ----------
        process : Process
            A fully initialised Process object.  Its `arrival` time
            determines when it first becomes eligible for the CPU.
        """
        with self._lock:
            self.processes.append(process)

    def tick(self) -> dict:
        """
        Advance the simulation clock by one time unit.

        Each call performs the following steps in order:

        1. **Admit** — any process whose arrival time ≤ current_time and
           that has not yet been queued is appended to the ready queue.
        2. **Dispatch** — if the CPU is free, dequeue the next process
           from the head of the ready queue.
        3. **Execute** — decrement the running process's remaining burst
           time by 1 and record the interval in the Gantt log.
        4. **Finish** — if remaining == 0 the process is marked done and
           its finish_time, turnaround, and waiting_time are computed.
        5. **Preempt** — else if the process has used a full quantum,
           admit any newly arrived processes first, then push the
           preempted process to the back of the ready queue.
        6. **Idle** — if no process is available, record an IDLE slot in
           the Gantt chart.
        7. Increment current_time and return a snapshot.

        Returns
        -------
        dict
            A snapshot of the scheduler state after this tick.
        """
        with self._lock:
            t = self.current_time

            # ── Step 1 : admit newly arrived processes ────────────────────────
            for p in self.processes:
                if (p.arrival <= t
                        and p.pid not in self._admitted_pids
                        and not p.is_done()):
                    self.ready_queue.append(p)
                    self._admitted_pids.add(p.pid)

            # ── Step 2 : dispatch from ready queue if CPU is free ─────────────
            if self._current_proc is None or self._current_proc.is_done():
                # clear a just-finished process sitting on the CPU slot
                if self._current_proc and self._current_proc.is_done():
                    self._current_proc = None

                if self.ready_queue:
                    self._current_proc    = self.ready_queue.popleft()
                    self._time_in_quantum = 0   # fresh quantum for new process

            # ── Step 3 : execute one unit of the running process ──────────────
            if self._current_proc:
                p = self._current_proc

                # record first-time-on-CPU
                if p.start_time is None:
                    p.start_time = t

                # consume one unit of burst
                p.remaining           -= 1
                self._time_in_quantum += 1

                # update Gantt: extend the last bar if it belongs to the same
                # process and ends exactly at t (i.e. consecutive ticks),
                # otherwise open a new bar.
                if (self.gantt
                        and self.gantt[-1][0] == p.pid
                        and self.gantt[-1][2] == t):
                    self.gantt[-1] = (p.pid, self.gantt[-1][1], t + 1)
                else:
                    self.gantt.append((p.pid, t, t + 1))

                # ── Step 4 : check for process completion ─────────────────────
                if p.is_done():
                    p.finish_time  = t + 1
                    p.turnaround   = p.finish_time - p.arrival
                    p.waiting_time = p.turnaround  - p.burst
                    self._finished.append(p)
                    self._current_proc = None

                # ── Step 5 : preempt when quantum is exhausted ────────────────
                elif self._time_in_quantum >= self.quantum:
                    # admit any process that arrived during this quantum
                    # BEFORE re-queueing the preempted one, so that processes
                    # arriving at time t+1 are placed ahead in the queue.
                    for new_p in self.processes:
                        if (new_p.arrival <= t + 1
                                and new_p.pid not in self._admitted_pids
                                and not new_p.is_done()):
                            self.ready_queue.append(new_p)
                            self._admitted_pids.add(new_p.pid)

                    # send the preempted process to the back
                    self.ready_queue.append(p)
                    self._current_proc    = None
                    self._time_in_quantum = 0

            else:
                # ── Step 6 : CPU is idle — no runnable process ────────────────
                # Merge with the previous IDLE bar if adjacent.
                if (self.gantt
                        and self.gantt[-1][0] == "IDLE"
                        and self.gantt[-1][2] == t):
                    self.gantt[-1] = ("IDLE", self.gantt[-1][1], t + 1)
                else:
                    self.gantt.append(("IDLE", t, t + 1))

            # ── Step 7 : advance clock and return snapshot ────────────────────
            self.current_time += 1
            return self._snapshot()

    def simulate_all(self) -> dict:
        """
        Run the simulation to completion without live timing.

        Repeatedly calls tick() until every registered process has finished
        and neither the ready queue nor the CPU holds an active process.

        Returns
        -------
        dict
            The final snapshot after the last tick (same schema as tick()).
        """
        snap = {}
        while True:
            # stop when all work is done and the CPU + queue are both empty
            if (self.all_done()
                    and not self.ready_queue
                    and self._current_proc is None):
                break

            snap = self.tick()

            # safety guard — should never be reached in normal usage
            if self.current_time > 10_000:
                break

        return snap

    def all_done(self) -> bool:
        """
        Return True when every registered process has completed.

        Returns False if no processes have been registered yet (the
        scheduler hasn't started meaningful work).
        """
        with self._lock:
            added = list(self.processes)
        return bool(added) and all(p.is_done() for p in added)

    #  Private helpers
    def _snapshot(self) -> dict:
        """
        Build and return a serialisable snapshot of the current state.

        Called at the end of every tick() while the lock is still held.

        Returns
        -------
        dict with keys:
            time    : int   – clock value after this tick
            gantt   : list  – copy of the full Gantt log
            procs   : list  – per-process snapshot dicts
            ready_q : list  – ordered list of pids in the ready queue
            running : str | None – pid currently on CPU, or None
        """
        return {
            "time"    : self.current_time,
            "gantt"   : list(self.gantt),
            "procs"   : [self._proc_snap(p) for p in self.processes],
            "ready_q" : [p.pid for p in list(self.ready_queue)],
            "running" : self._current_proc.pid if self._current_proc else None,
        }

    @staticmethod
    def _proc_snap(p: Process) -> dict:
        """
        Serialise a single Process into a plain dict.

        Waiting time and turnaround are only available once the process has
        finished; they are returned as None until that point.

        Returns
        -------
        dict with keys:
            pid       : str
            arrival   : int
            burst     : int  – original (unchanged)
            remaining : int  – CPU time still needed
            finish    : int | None
            wt        : float | None – waiting time (None if not done)
            tat       : float | None – turnaround time (None if not done)
            done      : bool
        """
        return {
            "pid"      : p.pid,
            "arrival"  : p.arrival,
            "burst"    : p.burst,
            "remaining": p.remaining,
            "finish"   : p.finish_time,
            "wt"       : p.waiting_time if p.is_done() else None,
            "tat"      : p.turnaround   if p.is_done() else None,
            "done"     : p.is_done(),
        }

    def __repr__(self) -> str:
        return (
            f"RoundRobinScheduler(quantum={self.quantum}, "
            f"time={self.current_time}, "
            f"processes={len(self.processes)})"
        )