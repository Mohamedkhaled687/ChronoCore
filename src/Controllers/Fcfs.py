from copy import deepcopy
from typing import List, Tuple, Dict

def fcfs(processes: List[Process]) -> ScheduleResult:
    # Work on a copy (don’t mutate input)
    procs = deepcopy(processes)

    # Sort by arrival time, then PID for stability
    procs.sort(key=lambda p: (p.arrival, p.pid))

    time = 0.0
    gantt: List[GanttEntry] = []
    completion: Dict[str, float] = {}

    for p in procs:
        # CPU idle → jump to next arrival
        if time < p.arrival:
            time = p.arrival

        start_time = time
        end_time = time + p.burst

        # Update time
        time = end_time

        # Store completion
        completion[p.pid] = end_time

        # Build Gantt entry
        gantt.append(GanttEntry(
            pid=p.pid,
            start=start_time,
            end=end_time,
            is_context_switch=False
        ))

    # Build final results using helper
    results, avg_wt, avg_tat = _make_results(procs, completion)

    return ScheduleResult(
        gantt=gantt,
        processes=results,
        avg_waiting_time=avg_wt,
        avg_turnaround_time=avg_tat
    )