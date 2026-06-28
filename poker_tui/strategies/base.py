from abc import ABC, abstractmethod

from poker_tui.domain.action import Action
from poker_tui.engine.public_state import PlayerView, PublicGameState


class AbstractStrategy(ABC):
    """Interface for bot strategies.

    Implement ``choose_action`` to decide what a bot does each turn.
    The engine calls this with a filtered view — opponents' hole cards
    are hidden before showdown.
    """

    @abstractmethod
    def choose_action(
        self,
        state: PublicGameState,
        player: PlayerView,
        legal_actions: list[Action],
    ) -> Action:
        ...
