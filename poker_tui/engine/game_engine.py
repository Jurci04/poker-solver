import random
from collections.abc import Mapping

from poker_tui.domain.action import Action
from poker_tui.domain.deck import Deck
from poker_tui.domain.enums import ActionType, PlayerStatus, Street
from poker_tui.domain.player import Player
from poker_tui.domain.table import Table
from poker_tui.engine.betting import BIG_BLIND, SMALL_BLIND, BettingRound, get_legal_actions
from poker_tui.engine.events import (
    BlindsPosted,
    CardsDealt,
    EventBus,
    HandEnded,
    HandStarted,
    PlayerActed,
    ShowdownStarted,
    StreetAdvanced,
)
from poker_tui.engine.hand_evaluator import HandEvaluator
from poker_tui.engine.state import GameState
from poker_tui.engine.visibility import VisibilityFilter
from poker_tui.strategies.base import AbstractStrategy


class GameEngine:
    """Drives a single poker table: blinds, dealing, betting rounds, showdown.

    Supports both automated (bot) and human play. Human players have no
    strategy assigned — the engine sets ``waiting_for_human`` and the
    caller must call ``handle_human_action`` to proceed.
    """

    def __init__(
        self,
        table: Table,
        strategies: Mapping[str, AbstractStrategy],
        rng: random.Random | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._table = table
        self._strategies = strategies
        self._rng = rng or random.Random()
        self._deck = Deck(rng=self._rng)
        self._state = GameState(table=table, event_bus=event_bus or EventBus())
        self._betting = BettingRound(table)
        self._current_player_idx = 0
        self._waiting_for_human = False
        self._hand_over = False

    @property
    def state(self) -> GameState:
        return self._state

    @property
    def event_bus(self) -> EventBus:
        return self._state.event_bus

    @property
    def hand_over(self) -> bool:
        return self._hand_over

    @property
    def waiting_for_human(self) -> bool:
        return self._waiting_for_human

    # ---- hand lifecycle ----

    def init_new_hand(self) -> None:
        """Set up a new hand: rotate dealer, post blinds, deal hole cards."""
        self._hand_over = False
        self._waiting_for_human = False
        self._state.next_hand()
        self._rotate_dealer()
        self._deck.reset()
        self._betting = BettingRound(self._table)
        self._post_blinds()
        self._deal_hole_cards()
        self._current_player_idx = self._get_first_to_act()
        self.event_bus.publish(HandStarted(
            hand_number=self._state.hand_number,
            player_count=sum(1 for p in self._table.players if not p.is_out),
        ))

    def play_hand(self) -> None:
        """Run a full hand automatically (for headless simulation)."""
        self.init_new_hand()
        while not self._hand_over:
            self._play_step()

    def step(self) -> bool:
        """Advance one game tick. Returns False when hand is over."""
        if self._hand_over:
            return False
        if self._waiting_for_human:
            return True
        self._play_step()
        return True

    def handle_human_action(self, player: Player, action: Action) -> None:
        """Apply a human-chosen action and resume the game loop."""
        self._waiting_for_human = False
        self.handle_action(player, action)

    # ---- dealer rotation and blind posting ----

    def _rotate_dealer(self) -> None:
        n = len(self._table.players)
        if self._state.hand_number > 1:
            self._table.dealer_position = (self._table.dealer_position + 1) % n
        self._table.players[self._table.dealer_position].is_dealer = True

        sb_pos = self._next_active_position(self._table.dealer_position)
        bb_pos = self._next_active_position(sb_pos)
        self._table.players[sb_pos].is_small_blind = True
        self._table.players[bb_pos].is_big_blind = True

    def _next_active_position(self, pos: int) -> int:
        n = len(self._table.players)
        for i in range(1, n + 1):
            if not self._table.players[(pos + i) % n].is_out:
                return (pos + i) % n
        return pos

    def _next_acting_position(self, pos: int) -> int:
        n = len(self._table.players)
        for i in range(1, n + 1):
            p = self._table.players[(pos + i) % n]
            if p.is_active and not p.is_folded and not p.is_out:
                return (pos + i) % n
        return pos

    def _post_blinds(self) -> None:
        for p in self._table.players:
            if p.is_small_blind:
                p.post_blind(SMALL_BLIND)
            if p.is_big_blind:
                p.post_blind(BIG_BLIND)
        self._state.pot.total = sum(p.total_bet_this_hand for p in self._table.players)
        active = [p for p in self._table.players if not p.is_folded and not p.is_out]
        self._state.pot.current_bet = max(p.current_bet for p in active)
        self.event_bus.publish(BlindsPosted(
            small_blind=SMALL_BLIND, big_blind=BIG_BLIND,
            dealer_pos=self._table.dealer_position,
        ))

    def _deal_hole_cards(self) -> None:
        for p in self._table.players:
            if not p.is_out:
                for card in self._deck.deal(2):
                    p.hand.add_card(card)
        self.event_bus.publish(CardsDealt(
            player_cards={
                p.name: [str(c) for c in p.hand.cards]
                for p in self._table.players if not p.is_out
            }
        ))

    # ---- turn order ----

    def _get_first_to_act(self) -> int:
        """Return the table index of the first player to act on the current street."""
        if self._state.street == Street.PREFLOP:
            bb_idx = next(i for i, p in enumerate(self._table.players) if p.is_big_blind)
            return self._next_acting_position(bb_idx)
        return self._next_acting_position(self._table.dealer_position)

    def get_current_player(self) -> Player | None:
        if self._current_player_idx >= len(self._table.players):
            return None
        return self._table.players[self._current_player_idx]

    def get_legal_actions_for_current(self) -> list[Action]:
        player = self.get_current_player()
        return get_legal_actions(player, self._table, self._betting.raise_count) if player else []

    def current_player_turn(self) -> Player | None:
        active = self._table.active_players
        if len(active) <= 1 and self._state.street != Street.SHOWDOWN:
            return None
        return self.get_current_player()

    # ---- action processing ----

    def handle_action(self, player: Player, action: Action) -> None:
        if player.is_folded or player.is_out:
            return

        self._betting.process_action(player, action)
        self.event_bus.publish(PlayerActed(player_name=player.name, action=action))

        self._state.pot.total = sum(p.total_bet_this_hand for p in self._table.players)
        active = [p for p in self._table.players if not p.is_folded and not p.is_out]
        self._state.pot.current_bet = max(p.current_bet for p in active)

        if action.action_type == ActionType.FOLD and len(self._table.players_in_hand) <= 1:
            self._hand_over = True
            winners = self._table.players_in_hand
            self._finish_hand(winners)

    def advance_to_next_player(self) -> bool:
        """Advance to the next active player or street. Returns False if hand ends."""
        if self._hand_over:
            return False
        if self._betting.complete:
            return self._advance_street_or_showdown()

        self._current_player_idx = self._next_acting_position(self._current_player_idx)

        # Full rotation completed.
        if self._current_player_idx == self._get_first_to_act() and self._betting.complete:
            return self._advance_street_or_showdown()

        # Skip folded / out players.
        player = self._table.players[self._current_player_idx]
        if player.is_folded or player.is_out:
            return self.advance_to_next_player()

        return True

    # ---- street advancement ----

    def _advance_street_or_showdown(self) -> bool:
        if self._state.street == Street.RIVER:
            return self._go_to_showdown()

        self._state.advance_street()
        self._betting = BettingRound(self._table)

        if self._state.street == Street.FLOP:
            self._deck.burn()
            for c in self._deck.deal(3):
                self._table.add_community_card(c)
        else:  # TURN or RIVER
            self._deck.burn()
            for c in self._deck.deal(1):
                self._table.add_community_card(c)

        self.event_bus.publish(StreetAdvanced(
            street=self._state.street,
            community_cards=[str(c) for c in self._table.community_cards],
        ))
        self._current_player_idx = self._get_first_to_act()
        return True

    # ---- showdown and pot award ----

    def _go_to_showdown(self) -> bool:
        self._state.street = Street.SHOWDOWN
        contestants = self._table.players_in_hand

        if len(contestants) <= 1:
            self._hand_over = True
            self._finish_hand(contestants)
            return False

        self.event_bus.publish(ShowdownStarted(
            players=[{"name": p.name, "hand": [str(c) for c in p.hand.cards]} for p in contestants],
        ))

        hands = [(p.name, p.hand.cards + self._table.community_cards) for p in contestants]
        winners = HandEvaluator.find_winners(hands)
        self._hand_over = True
        self._finish_hand([p for p in contestants if p.name in winners])
        return False

    def _finish_hand(self, winners: list[Player]) -> None:
        winner_list: list[dict[str, str | int]] = []
        if winners:
            split = self._state.pot.total // len(winners)
            remainder = self._state.pot.total - split * len(winners)
            for i, w in enumerate(winners):
                amount = split + (remainder if i == 0 else 0)
                w.win_pot(amount)
                winner_list.append({"name": w.name, "amount": amount})

        for p in self._table.players:
            if p.stack <= 0 and not p.is_out:
                p.status = PlayerStatus.OUT

        self.event_bus.publish(HandEnded(
            winners=winner_list,
            pot_amount=self._state.pot.total,
            hand_number=self._state.hand_number,
        ))

    # ---- internal step ----

    def _play_step(self) -> None:
        player = self.current_player_turn()
        if player is None:
            if not self._advance_street_or_showdown():
                return
            player = self.current_player_turn()
            if player is None:
                return

        strategy = self._strategies.get(player.name)
        if strategy is None:
            self._waiting_for_human = True
            return

        legal = get_legal_actions(player, self._table, self._betting.raise_count)
        if not legal:
            self._hand_over = True
            return

        pub = VisibilityFilter.player_state(
            self._table, player, self._state.pot.total, self._state.pot.current_bet,
            self._state.street, self._state.hand_number, legal,
        )
        pv = pub.get_player_view(player.name)
        if pv is not None:
            action = strategy.choose_action(pub, pv, legal)
            self.handle_action(player, action)
            self.advance_to_next_player()
