from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from poker_tui.domain.action import Action
from poker_tui.domain.enums import Street


@dataclass
class HandStarted:
    """Published when a new hand begins."""
    name: str = "hand_started"
    hand_number: int = 0
    player_count: int = 0


@dataclass
class BlindsPosted:
    """Published after small blind and big blind are taken."""
    name: str = "blinds_posted"
    small_blind: int = 0
    big_blind: int = 0
    dealer_pos: int = 0


@dataclass
class CardsDealt:
    """Published when hole cards are dealt."""
    name: str = "cards_dealt"
    player_cards: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class PlayerActed:
    """Published after a player completes an action."""
    name: str = "player_acted"
    player_name: str = ""
    action: Action = field(default_factory=lambda: Action.fold())


@dataclass
class StreetAdvanced:
    """Published when the hand moves to the next street."""
    name: str = "street_advanced"
    street: Street = Street.PREFLOP
    community_cards: list[str] = field(default_factory=list)


@dataclass
class ShowdownStarted:
    """Published when remaining players reveal their hands."""
    name: str = "showdown_started"
    players: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class HandEnded:
    """Published when a hand is complete with winner info."""
    name: str = "hand_ended"
    winners: list[dict[str, Any]] = field(default_factory=list)
    pot_amount: int = 0
    hand_number: int = 0


EventListener = Callable[..., None]


class EventBus:
    """Simple pub/sub event bus. Consumers subscribe by event name string."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[EventListener]] = {}

    def subscribe(self, event_name: str, listener: EventListener) -> None:
        self._listeners.setdefault(event_name, []).append(listener)

    def publish(self, event: object) -> None:
        name = getattr(event, "name", "unknown")
        for listener in self._listeners.get(name, []):
            listener(event)
