from poker_tui.domain.action import Action
from poker_tui.domain.enums import ActionType
from poker_tui.engine.public_state import PlayerView, PublicGameState
from poker_tui.strategies.base import AbstractStrategy


class PlaceholderStrategy(AbstractStrategy):
    """Minimal deterministic strategy: check when possible, call small bets,
    otherwise fold. This is a placeholder for future strategy implementations."""

    def choose_action(
        self,
        state: PublicGameState,
        player: PlayerView,
        legal_actions: list[Action],
    ) -> Action:
        for a in legal_actions:
            if a.action_type == ActionType.CHECK:
                return a
        for a in legal_actions:
            if a.action_type == ActionType.CALL and a.amount <= 40:
                return a
        for a in legal_actions:
            if a.action_type == ActionType.CALL:
                return a
        return legal_actions[0] if legal_actions else Action.fold()
