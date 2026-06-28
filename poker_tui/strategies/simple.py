"""Simple deterministic poker strategy for testing the TUI and engine.

Hand assessment
    Preflop — uses hole-card heuristics (pair rank, high cards, suitedness).
    Postflop — uses ``HandEvaluator`` to get the best 5-card rank.

Action selection
    Check available   → bet/raise strong hands, check medium, fold weak.
    Facing a bet/call → call medium, fold weak, re-raise very strong.
    Re-raises are safe because the engine caps raises at 2 per street.
"""

from poker_tui.domain.action import Action
from poker_tui.domain.enums import ActionType
from poker_tui.engine.hand_evaluator import HandEvaluator, HandRank
from poker_tui.engine.public_state import PlayerView, PublicGameState
from poker_tui.strategies.base import AbstractStrategy


def _pick(
    by_type: dict[ActionType, Action],
    *types: ActionType,
    or_else: Action,
) -> Action:
    for t in types:
        a = by_type.get(t)
        if a is not None:
            return a
    return or_else


def _can_check(by_type: dict[ActionType, Action]) -> bool:
    return ActionType.CHECK in by_type


def _hole_ranks(player: PlayerView) -> tuple[int, int, bool]:
    cards = player.hole_cards
    r1, r2 = sorted((c.rank.value for c in cards), reverse=True)
    suited = cards[0].suit == cards[1].suit
    return r1, r2, suited


class SimpleStrategy(AbstractStrategy):
    """Conservative bot: plays tight preflop, bets made hands, re-raises very strong."""

    def choose_action(
        self,
        state: PublicGameState,
        player: PlayerView,
        legal_actions: list[Action],
    ) -> Action:
        by_type: dict[ActionType, Action] = {a.action_type: a for a in legal_actions}
        fallback = legal_actions[0] if legal_actions else Action.fold()

        if state.street.name == "PREFLOP":
            return self._preflop(player, by_type, fallback)
        return self._postflop(state, player, by_type, fallback)

    def _preflop(
        self,
        player: PlayerView,
        by_type: dict[ActionType, Action],
        fallback: Action,
    ) -> Action:
        if len(player.hole_cards) < 2:
            return fallback

        r1, r2, suited = _hole_ranks(player)
        is_pair = r1 == r2

        strong = (
            (is_pair and r1 >= 10)
            or (r1 >= 12 and r2 >= 12)
            or (suited and r1 == 14 and r2 == 13)
        )
        medium = (
            is_pair
            or r1 + r2 >= 26
            or (suited and r1 + r2 >= 24)
            or (suited and r1 - r2 <= 2 and r2 >= 8)
        )

        can_check = _can_check(by_type)

        if strong:
            if can_check:
                return _pick(by_type, ActionType.RAISE, ActionType.BET, or_else=fallback)
            return _pick(by_type, ActionType.RAISE, ActionType.CALL, or_else=fallback)

        if can_check:
            if medium:
                return _pick(by_type, ActionType.CHECK, ActionType.CALL, or_else=fallback)
            return _pick(by_type, ActionType.CHECK, ActionType.FOLD, or_else=fallback)

        if medium:
            return _pick(by_type, ActionType.CALL, ActionType.CHECK, or_else=fallback)

        return _pick(by_type, ActionType.FOLD, ActionType.CHECK, or_else=fallback)

    def _postflop(
        self,
        state: PublicGameState,
        player: PlayerView,
        by_type: dict[ActionType, Action],
        fallback: Action,
    ) -> Action:
        all_cards = player.hole_cards + state.community_cards
        if len(all_cards) < 5:
            return _pick(by_type, ActionType.CHECK, ActionType.CALL, or_else=fallback)

        rank, _ = HandEvaluator.evaluate(all_cards)
        can_check = _can_check(by_type)

        if rank >= HandRank.STRAIGHT:
            if can_check:
                return _pick(by_type, ActionType.BET, ActionType.RAISE, or_else=fallback)
            return _pick(by_type, ActionType.RAISE, ActionType.CALL, or_else=fallback)

        if rank >= HandRank.THREE_OF_A_KIND:
            if can_check:
                return _pick(by_type, ActionType.BET, ActionType.CHECK, or_else=fallback)
            call = by_type.get(ActionType.CALL)
            if call and call.amount > state.pot_total:
                return _pick(by_type, ActionType.FOLD, or_else=fallback)
            return _pick(by_type, ActionType.CALL, ActionType.CHECK, or_else=fallback)

        if rank >= HandRank.TWO_PAIR:
            return _pick(by_type, ActionType.CHECK, ActionType.CALL, or_else=fallback)

        if rank == HandRank.PAIR:
            if can_check:
                return _pick(by_type, ActionType.CHECK, or_else=fallback)
            call = by_type.get(ActionType.CALL)
            if call and call.amount > state.pot_total // 2:
                return _pick(by_type, ActionType.FOLD, or_else=fallback)
            return _pick(by_type, ActionType.CALL, ActionType.CHECK, or_else=fallback)

        if can_check:
            return _pick(by_type, ActionType.CHECK, or_else=fallback)
        return _pick(by_type, ActionType.FOLD, or_else=fallback)
