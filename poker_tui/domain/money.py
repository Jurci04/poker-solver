from dataclasses import dataclass
from typing import Any


@dataclass
class Pot:
    """Tracks the main pot total and current round bet size."""
    total: int = 0
    current_bet: int = 0

    def add_bet(self, amount: int) -> None:
        self.total += amount

    def reset_round(self) -> None:
        self.current_bet = 0

    def reset(self) -> None:
        self.total = 0
        self.current_bet = 0

    def __str__(self) -> str:
        return f"Pot: {self.total}"

    def to_dict(self) -> dict[str, Any]:
        return {"total": self.total, "current_bet": self.current_bet}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Pot":
        return cls(total=data["total"], current_bet=data.get("current_bet", 0))
