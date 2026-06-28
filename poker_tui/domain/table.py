from dataclasses import dataclass, field
from typing import Any

from poker_tui.domain.card import Card
from poker_tui.domain.player import Player


@dataclass
class Table:
    """A poker table holding players, community cards, and the dealer marker."""
    players: list[Player]
    community_cards: list[Card] = field(default_factory=list)
    dealer_position: int = 0

    @property
    def active_players(self) -> list[Player]:
        return [p for p in self.players if p.is_active and not p.is_folded and not p.is_out]

    @property
    def players_in_hand(self) -> list[Player]:
        return [p for p in self.players if not p.is_folded and not p.is_out]

    @property
    def player_count(self) -> int:
        return len([p for p in self.players if not p.is_out])

    def add_community_card(self, card: Card) -> None:
        self.community_cards.append(card)

    def reset_community(self) -> None:
        self.community_cards = []

    def __str__(self) -> str:
        return (
            f"Table({self.player_count} players, "
            f"community: {' '.join(str(c) for c in self.community_cards) or 'none'})"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "players": [p.to_dict() for p in self.players],
            "community_cards": [c.to_dict() for c in self.community_cards],
            "dealer_position": self.dealer_position,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Table":
        return cls(
            players=[Player.from_dict(p) for p in data["players"]],
            community_cards=[Card.from_dict(c) for c in data["community_cards"]],
            dealer_position=data["dealer_position"],
        )
