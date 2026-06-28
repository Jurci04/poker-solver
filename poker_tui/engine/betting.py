"""Fixed-limit betting with a two-raise cap (bet + one re-raise).

Constants
    BIG_BLIND / SMALL_BLIND — posted by the two players after the button.
    MIN_BET                — size of a single bet.
    MIN_RAISE              — size of the first raise; the re-raise is 2× this.

Raise rule (per street)
    • BET (raise_count 0 → 1): amount = MIN_BET
    • RAISE (raise_count 1 → 2): amount = current_bet + MIN_RAISE
    • RE-RAISE (raise_count 2 → 3, capped at 2): amount = current_bet + MIN_RAISE × 2
    • No further raises once raise_count >= 2.
"""

from poker_tui.domain.action import Action
from poker_tui.domain.enums import ActionType, PlayerStatus
from poker_tui.domain.player import Player
from poker_tui.domain.table import Table

BIG_BLIND = 20
SMALL_BLIND = 10
MIN_BET = 20
MIN_RAISE = 20

MAX_RAISES = 2


def get_legal_actions(
    player: Player,
    table: Table,
    raise_count: int = 0,
) -> list[Action]:
    """Return legal actions for *player*, optionally given the current raise count."""
    if not player.is_active:
        return []

    active = [p for p in table.players if not p.is_folded and not p.is_out]
    if not active:
        return []

    current_bet = max(p.current_bet for p in active)
    to_call = current_bet - player.current_bet
    actions = [Action.fold()]

    if to_call == 0:
        actions.append(Action.check())
    else:
        actions.append(Action.call(min(to_call, player.stack)))

    if to_call == 0 and player.stack >= MIN_BET:
        actions.append(Action.bet(MIN_BET))

    can_raise = raise_count < MAX_RAISES and player.stack > to_call
    if can_raise and (to_call > 0 or raise_count > 0):
        add = MIN_RAISE * (1 + raise_count)
        target = current_bet + add
        if target - player.current_bet <= player.stack:
            actions.append(Action.raise_(target))

    if player.stack > 0 and not any(a.is_all_in for a in actions):
        actions.append(Action.all_in(player.stack))

    return actions


class BettingRound:
    """Tracks who has acted and whether the current betting round is complete.

    Also tracks the number of raises to enforce the two-raise cap.
    """

    def __init__(self, table: Table) -> None:
        self._table = table
        for p in table.players:
            p.current_bet = 0
        self._last_raiser: Player | None = None
        self._players_acted: set[int] = set()
        self._raise_count: int = 0

    @property
    def raise_count(self) -> int:
        return self._raise_count

    @property
    def complete(self) -> bool:
        active = [p for p in self._table.players if p.is_active]
        if len(active) <= 1:
            return True
        if not all(id(p) in self._players_acted for p in active):
            return False
        if self._last_raiser is None:
            return len({p.current_bet for p in active}) == 1
        return all(
            p is self._last_raiser or p.current_bet == self._last_raiser.current_bet
            for p in active
        )

    def process_action(self, player: Player, action: Action) -> None:
        if not player.is_active:
            return

        self._players_acted.add(id(player))

        if action.action_type == ActionType.FOLD:
            player.status = PlayerStatus.FOLDED
            return
        elif action.action_type == ActionType.CALL:
            player.post_bet(action.amount)
        elif action.action_type == ActionType.RAISE:
            player.post_bet(action.amount - player.current_bet)
            self._last_raiser = player
            self._raise_count += 1
        elif action.action_type == ActionType.BET:
            player.post_bet(action.amount)
            self._last_raiser = player
            self._raise_count += 1
        elif action.action_type == ActionType.ALL_IN:
            player.post_bet(action.amount)

        if player.stack == 0:
            player.status = PlayerStatus.ALL_IN
