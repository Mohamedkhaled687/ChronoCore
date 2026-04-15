import copy
from typing import List
from Input_output_format import Process, ScheduleResult, GanttEntry, _make_results

def sjf_non_preemptive(processes: List[Process]) -> ScheduleResult:
    """
    Non-preemptive SJF: Once a process starts, it holds the CPU until the 
    end of its burst[cite: 11, 23].
    """
    procs = copy.deepcopy(processes)
    time = min(p.arrival for p in procs) if procs else 0
    gantt, completion = [], {}
    
    finished_count = 0
    num_procs = len(procs)

    while finished_count < num_procs:
        # 1. Identify processes that have arrived and are not finished
        available = [p for p in procs if p.arrival <= time and p.pid not in completion]

        if not available:
            # CPU is idle; jump to the next arrival time
            time = min(p.arrival for p in procs if p.pid not in completion)
            continue

        # 2. Selection: Choose the process with the shortest burst time [cite: 3, 5]
        p = min(available, key=lambda x: x.burst)

        # 3. Execution: Non-preemptive means it runs for the full burst 
        start_time = time
        duration = p.burst
        time = round(time + duration, 10)
        
        # 4. Record state
        p.remaining = 0
        completion[p.pid] = time
        gantt.append(GanttEntry(p.pid, start_time, time))
        finished_count += 1

    results, avg_wt, avg_tat = _make_results(procs, completion)
    return ScheduleResult(gantt, results, avg_wt, avg_tat)


def sjf_preemptive(processes: List[Process]) -> ScheduleResult:
    """
    Preemptive SJF (Shortest-Remaining-Time-First): If a new process arrives with 
    a shorter burst than the current process, it preempts the CPU[cite: 48, 66].
    """
    procs = copy.deepcopy(processes)
    time = min(p.arrival for p in procs) if procs else 0
    gantt, completion = [], {}

    while any(p.remaining > 0 for p in procs):
        # 1. Identify arrived processes with remaining burst 
        available = [p for p in procs if p.arrival <= time and p.remaining > 0]

        if not available:
            time = min(p.arrival for p in procs if p.remaining > 0)
            continue

        # 2. Selection: Choose process with shortest remaining time [cite: 38, 48]
        p = min(available, key=lambda x: x.remaining)

        # 3. Determine step: Run for 1 unit or until a new process arrives
        # Check if a new process arrives before the current one finishes
        next_arrivals = [q.arrival for q in procs if q.arrival > time and q.remaining > 0]
        limit = min(next_arrivals) - time if next_arrivals else float('inf')
        
        # We step by the smallest of: remaining burst or time until next arrival
        step = min(p.remaining, limit)
        # Ensure minimum step for simulation granularity (e.g., 0.1)
        if step == 0 and p.remaining > 0: step = p.remaining 

        # 4. Record in Gantt (Merge blocks if the same process continues) [cite: 83]
        if gantt and gantt[-1].pid == p.pid:
            gantt[-1].end = round(time + step, 10)
        else:
            gantt.append(GanttEntry(p.pid, time, round(time + step, 10)))

        # 5. Update state
        time = round(time + step, 10)
        p.remaining = round(p.remaining - step, 10)

        if p.remaining <= 0:
            completion[p.pid] = time

    results, avg_wt, avg_tat = _make_results(procs, completion)
    return ScheduleResult(gantt, results, avg_wt, avg_tat)