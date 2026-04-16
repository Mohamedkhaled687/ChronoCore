"""Deterministic scheduler engine tests."""

from src.Controllers.engines import EngineConfig, EngineFactory
from src.Models import ProcessSpec


def _build_processes(rows):
    return [
        ProcessSpec(
            pid=pid,
            arrival_time=arrival,
            burst_time=burst,
            priority=priority,
            insertion_order=i,
        )
        for i, (pid, arrival, burst, priority) in enumerate(rows)
    ]


def _metrics_map(result):
    return {m.pid: m for m in result.process_metrics}


def test_fcfs_order():
    engine = EngineFactory.create("fcfs")
    processes = _build_processes([
        ("P1", 0, 4, None),
        ("P2", 1, 3, None),
        ("P3", 2, 1, None),
    ])
    result = engine.compute_static(processes, EngineConfig())
    assert [s.pid for s in result.timeline] == ["P1", "P2", "P3"]


def test_sjf_non_preemptive():
    engine = EngineFactory.create("sjf")
    processes = _build_processes([
        ("P1", 0, 8, None),
        ("P2", 1, 4, None),
        ("P3", 2, 2, None),
    ])
    result = engine.compute_static(processes, EngineConfig(preemptive=False))
    assert [s.pid for s in result.timeline] == ["P1", "P3", "P2"]


def test_sjf_preemptive_srtf():
    engine = EngineFactory.create("sjf")
    processes = _build_processes([
        ("P1", 0, 8, None),
        ("P2", 1, 4, None),
        ("P3", 2, 2, None),
    ])
    result = engine.compute_static(processes, EngineConfig(preemptive=True))
    assert [s.pid for s in result.timeline][:3] == ["P1", "P2", "P3"]
    mm = _metrics_map(result)
    assert mm["P3"].turnaround_time <= mm["P2"].turnaround_time


def test_priority_fcfs_tie_break():
    engine = EngineFactory.create("priority")
    processes = _build_processes([
        ("P1", 0, 3, 1),
        ("P2", 1, 2, 1),
        ("P3", 2, 1, 0),
    ])
    result = engine.compute_static(processes, EngineConfig(preemptive=False))
    assert [s.pid for s in result.timeline] == ["P1", "P3", "P2"]


def test_round_robin_quantum():
    engine = EngineFactory.create("round_robin")
    processes = _build_processes([
        ("P1", 0, 5, None),
        ("P2", 0, 3, None),
    ])
    result = engine.compute_static(processes, EngineConfig(quantum=2.0))
    assert [s.pid for s in result.timeline] == ["P1", "P2", "P1", "P2", "P1"]
