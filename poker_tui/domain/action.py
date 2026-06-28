from dataclasses import dataclass
from typing import Any

from poker_tui.domain.enums import ActionType


@dataclass(frozen=True)
class Action:
    """Represents a player action with optional chip amount. Immutable."""
    action_type: ActionType
    amount: int = 0

    def __str__(self) -> str:
        if self.action_type in (ActionType.FOLD, ActionType.CHECK):
            return self.action_type.name
        return f"{self.action_type.name} {self.amount}"

    @property
    def is_all_in(self) -> bool:
        return self.action_type == ActionType.ALL_IN

    def to_dict(self) -> dict[str, Any]:
        return {"action_type": self.action_type.name, "amount": self.amount}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Action":
        return cls(action_type=ActionType[data["action_type"]], amount=data["amount"])

    @classmethod
    def fold(cls) -> "Action":
        return cls(action_type=ActionType.FOLD)

    @classmethod
    def check(cls) -> "Action":
        return cls(action_type=ActionType.CHECK)

    @classmethod
    def call(cls, amount: int = 0) -> "Action":
        return cls(action_type=ActionType.CALL, amount=amount)

    @classmethod
    def bet(cls, amount: int) -> "Action":
        return cls(action_type=ActionType.BET, amount=amount)

    @classmethod
    def raise_(cls, amount: int) -> "Action":
        return cls(action_type=ActionType.RAISE, amount=amount)

    @classmethod
    def all_in(cls, amount: int) -> "Action":
        return cls(action_type=ActionType.ALL_IN, amount=amount)
