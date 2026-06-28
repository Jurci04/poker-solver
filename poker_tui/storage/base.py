from abc import ABC, abstractmethod

from poker_tui.simulation.result import SimulationResult


class StorageBackend(ABC):
    """Interface for persistence. Swap implementations without touching the engine."""

    @abstractmethod
    def save(self, result: SimulationResult, path: str) -> None:
        ...

    @abstractmethod
    def load(self, path: str) -> SimulationResult:
        ...
