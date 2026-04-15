import copy
from typing import List
from Input_output_format import Process, ScheduleResult,GanttEntry,_make_results

def priority_preemptive(processes: List[Process], quantum: float = 2.0) -> ScheduleResult:
    procs = copy.deepcopy(processes)
    time = min(p.arrival for p in procs) if procs else 0
    gantt, completion = [], {}
    # Track when a process was last serviced to facilitate Round-Robin tie-breaking
    last_serviced = {p.pid: 0.0 for p in procs}

    while any(p.remaining > 0 for p in procs):
        # 1. Identify processes that have arrived and need CPU
        available = [p for p in procs if p.arrival <= time and p.remaining > 0]

        if not available:
            time = min(p.arrival for p in procs if p.remaining > 0)
            continue

        # 2. Selection: Highest priority first.
        # Tie-breaker: least recently serviced (RR)
        hp = min(p.priority for p in available)
        p = min([p for p in available if p.priority == hp], key=lambda x: last_serviced[x.pid])

        # 3. Determine execution duration (the "step")
        # Step is limited by: Quantum, Remaining burst, or Arrival of a HIGHER priority process
        higher_arrival = [q.arrival for q in procs if q.arrival > time and q.priority < hp and q.remaining > 0]
        limit = min(higher_arrival) - time if higher_arrival else float('inf')
        step = min(p.remaining, quantum, limit)

        # 4. Record in Gantt (Merge blocks if the same process continues)
        if gantt and gantt[-1].pid == p.pid:
            gantt[-1].end = round(time + step, 10)
        else:
            gantt.append(GanttEntry(p.pid, time, round(time + step, 10)))

        # 5. Update state
        time = round(time + step, 10)
        p.remaining = round(p.remaining - step, 10)
        last_serviced[p.pid] = time  # Move to the "back of the line" for this priority

        if p.remaining <= 0:
            completion[p.pid] = time

    results, avg_wt, avg_tat = _make_results(procs, completion)
    return ScheduleResult(gantt, results, avg_wt, avg_tat)
