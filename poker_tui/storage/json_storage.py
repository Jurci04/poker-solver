
import json

from poker_tui.simulation.result import SimulationResult
from poker_tui.storage.base import StorageBackend


class JsonStorage(StorageBackend):
    def save(self, result: SimulationResult, path: str) -> None:
        with open(path, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

    def load(self, path: str) -> SimulationResult:
        with open(path) as f:
            data = json.load(f)
        return SimulationResult.from_dict(data)
