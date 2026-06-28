from dataclasses import dataclass
from typing import Any

from poker_tui.domain.enums import Rank, Suit


@dataclass(frozen=True, order=True)
class Card:
    """A single playing card with a rank and suit. Frozen for immutability."""
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"

    def to_dict(self) -> dict[str, Any]:
        return {"rank": self.rank.value, "suit": self.suit.value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Card":
        return cls(rank=Rank(data["rank"]), suit=Suit(data["suit"]))
