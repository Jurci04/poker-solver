from dataclasses import dataclass
from typing import Any

from poker_tui.domain.card import Card


@dataclass
class Hand:
    """A collection of cards held by a player."""
    cards: list[Card]

    @classmethod
    def empty(cls) -> "Hand":
        return cls(cards=[])

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    def __len__(self) -> int:
        return len(self.cards)

    def __str__(self) -> str:
        return " ".join(str(c) for c in self.cards)

    def to_dict(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self.cards]

    @classmethod
    def from_dict(cls, data: list[dict[str, Any]]) -> "Hand":
        return cls(cards=[Card.from_dict(d) for d in data])
