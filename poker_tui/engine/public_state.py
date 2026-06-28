from dataclasses import dataclass, field

from poker_tui.domain.action import Action
from poker_tui.domain.card import Card
from poker_tui.domain.enums import Street


@dataclass
class PlayerView:
    """What a player (or observer) is allowed to see about a participant."""
    name: str
    stack: int
    position: int
    current_bet: int
    is_dealer: bool
    is_small_blind: bool
    is_big_blind: bool
    is_active: bool
    is_folded: bool
    hole_cards: list[Card] = field(default_factory=list)
    total_bet_this_hand: int = 0


@dataclass
class PublicGameState:
    """Filtered game state shown to strategies, human players, and observers."""
    community_cards: list[Card]
    pot_total: int
    current_bet: int
    street: Street
    hand_number: int
    players: list[PlayerView]
    current_player_name: str | None = None
    legal_actions: list[Action] = field(default_factory=list)

    def get_player_view(self, name: str) -> PlayerView | None:
        for p in self.players:
            if p.name == name:
                return p
        return None
