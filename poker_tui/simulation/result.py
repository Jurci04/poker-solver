from dataclasses import dataclass, field
from typing import Any


@dataclass
class SimulationResult:
    """Immutable snapshot of a completed simulation."""
    total_hands: int
    players: list[str] = field(default_factory=list)
    player_stats: dict[str, dict[str, Any]] = field(default_factory=dict)
    hand_results: list[dict[str, Any]] = field(default_factory=list)
    action_frequencies: dict[str, dict[str, int]] = field(default_factory=dict)
    seed: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_hands": self.total_hands,
            "players": self.players,
            "player_stats": self.player_stats,
            "hand_results": self.hand_results,
            "action_frequencies": self.action_frequencies,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SimulationResult":
        return cls(
            total_hands=data["total_hands"],
            players=data.get("players", []),
            player_stats=data.get("player_stats", {}),
            hand_results=data.get("hand_results", []),
            action_frequencies=data.get("action_frequencies", {}),
            seed=data.get("seed"),
        )
