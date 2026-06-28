from dataclasses import dataclass, field
from typing import Any

from poker_tui.domain.enums import PlayerStatus
from poker_tui.domain.hand import Hand


@dataclass
class Player:
    """A player at the table with stack, hand, position, and lifecycle status."""
    name: str
    stack: int = 1000
    position: int = 0
    status: PlayerStatus = PlayerStatus.ACTIVE
    hand: Hand = field(default_factory=Hand.empty)
    current_bet: int = 0
    total_bet_this_hand: int = 0
    is_dealer: bool = False
    is_small_blind: bool = False
    is_big_blind: bool = False
    strategy_name: str = "human"

    @property
    def is_active(self) -> bool:
        return self.status == PlayerStatus.ACTIVE

    @property
    def is_folded(self) -> bool:
        return self.status == PlayerStatus.FOLDED

    @property
    def is_out(self) -> bool:
        return self.status == PlayerStatus.OUT

    def reset_for_new_hand(self) -> None:
        self.hand = Hand.empty()
        self.current_bet = 0
        self.total_bet_this_hand = 0
        self.is_dealer = False
        self.is_small_blind = False
        self.is_big_blind = False
        if self.status != PlayerStatus.OUT:
            self.status = PlayerStatus.ACTIVE

    def post_blind(self, amount: int) -> int:
        """Subtract blind amount from stack, return chips actually taken."""
        actual = min(amount, self.stack)
        self.stack -= actual
        self.current_bet += actual
        self.total_bet_this_hand += actual
        return actual

    def post_bet(self, amount: int) -> int:
        """Subtract bet from stack, return chips actually taken."""
        actual = min(amount, self.stack)
        self.stack -= actual
        self.current_bet += actual
        self.total_bet_this_hand += actual
        return actual

    def win_pot(self, amount: int) -> None:
        self.stack += amount

    def reset_bet_for_round(self) -> None:
        self.current_bet = 0

    def __str__(self) -> str:
        return f"{self.name} (${self.stack})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "stack": self.stack,
            "position": self.position,
            "status": self.status.name,
            "hand": self.hand.to_dict(),
            "current_bet": self.current_bet,
            "total_bet_this_hand": self.total_bet_this_hand,
            "strategy_name": self.strategy_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Player":
        return cls(
            name=data["name"],
            stack=data["stack"],
            position=data["position"],
            status=PlayerStatus[data["status"]],
            hand=Hand.from_dict(data["hand"]),
            current_bet=data["current_bet"],
            total_bet_this_hand=data["total_bet_this_hand"],
            strategy_name=data.get("strategy_name", "human"),
        )
