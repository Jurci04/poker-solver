from dataclasses import dataclass, field

from poker_tui.domain.enums import Street
from poker_tui.domain.money import Pot
from poker_tui.domain.table import Table
from poker_tui.engine.events import EventBus


@dataclass
class GameState:
    """Aggregate state for a single poker game session."""
    table: Table
    pot: Pot = field(default_factory=Pot)
    street: Street = Street.PREFLOP
    hand_number: int = 0
    event_bus: EventBus = field(default_factory=EventBus)

    def next_hand(self) -> None:
        self.hand_number += 1
        self.street = Street.PREFLOP
        self.pot.reset()
        for p in self.table.players:
            p.reset_for_new_hand()
        self.table.reset_community()

    def advance_street(self) -> None:
        streets = [Street.PREFLOP, Street.FLOP, Street.TURN, Street.RIVER, Street.SHOWDOWN]
        idx = streets.index(self.street)
        if idx < len(streets) - 1:
            self.street = streets[idx + 1]
