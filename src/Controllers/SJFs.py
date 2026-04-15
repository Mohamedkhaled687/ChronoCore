import copy
from typing import List
from Input_output_format import Process, ScheduleResult, GanttEntry, _make_results

def run_sjf(processes: List[Process], preemptive: bool = False) -> ScheduleResult:
    """
    Unified SJF Algorithm.
    :param preemptive: If False, performs Non-preemptive SJF. 
                       If True, performs Shortest-Remaining-Time-First.
    """
    procs = copy.deepcopy(processes)
    # Start time is the arrival of the first process [cite: 27, 85]
    time = min(p.arrival for p in procs) if procs else 0
    gantt, completion = [], {}

    while any(p.remaining > 0 for p in procs):
        # 1. Identify processes that have arrived and need CPU [cite: 4, 67]
        available = [p for p in procs if p.arrival <= time and p.remaining > 0]

        if not available:
            # CPU is idle; jump to next arrival [cite: 28, 86]
            time = min(p.arrival for p in procs if p.remaining > 0)
            continue

        # 2. Selection: Pick the process with the shortest burst (SJF) 
        # or shortest remaining time (SRTF) [cite: 5, 38]
        p = min(available, key=lambda x: x.remaining)

        # 3. Determine execution duration (the "step")
        if not preemptive:
            # Non-preemptive: Run the full remaining burst 
            step = p.remaining
        else:
            # Preemptive: Run until a new process arrives that might be shorter [cite: 48, 67]
            next_arrivals = [q.arrival for q in procs if q.arrival > time and q.remaining > 0]
            limit = min(next_arrivals) - time if next_arrivals else float('inf')
            step = min(p.remaining, limit)

        # 4. Record in Gantt (Merge blocks if the same process continues) [cite: 84]
        if gantt and gantt[-1].pid == p.pid:
            gantt[-1].end = round(time + step, 10)
        else:
            gantt.append(GanttEntry(p.pid, time, round(time + step, 10)))

        # 5. Update state
        time = round(time + step, 10)
        p.remaining = round(p.remaining - step, 10)

        if p.remaining <= 0:
            completion[p.pid] = time
    # Generate results table, average waiting time, and turnaround time [cite: 32, 94]
    results, avg_wt, avg_tat = _make_results(procs, completion)
    return ScheduleResult(gantt, results, avg_wt, avg_tat)