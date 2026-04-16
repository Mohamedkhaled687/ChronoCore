"""Factory for constructing scheduler engines by algorithm key."""

from __future__ import annotations

from src.Controllers.engines.base_engine import BaseSchedulerEngine
from src.Controllers.engines.fcfs_engine import FCFSEngine
from src.Controllers.engines.priority_engine import PriorityEngine
from src.Controllers.engines.rr_engine import RoundRobinEngine
from src.Controllers.engines.sjf_engine import SJFEngine
from src.Models import AlgorithmKey


class EngineFactory:
    @staticmethod
    def create(algorithm: str) -> BaseSchedulerEngine:
        key = AlgorithmKey(algorithm)
        if key is AlgorithmKey.FCFS:
            return FCFSEngine()
        if key is AlgorithmKey.SJF:
            return SJFEngine()
        if key is AlgorithmKey.PRIORITY:
            return PriorityEngine()
        if key is AlgorithmKey.ROUND_ROBIN:
            return RoundRobinEngine()
        raise ValueError(f"Unsupported algorithm: {algorithm}")
