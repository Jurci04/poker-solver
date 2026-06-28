import random

from poker_tui.domain.enums import PlayerStatus
from poker_tui.domain.player import Player
from poker_tui.domain.table import Table
from poker_tui.engine.game_engine import GameEngine
from poker_tui.strategies.placeholder import PlaceholderStrategy


class TestEngine:
    def _make_engine(self, num_players: int = 3) -> GameEngine:
        players = [
            Player(name=f"Bot-{i}", stack=1000, position=i, strategy_name="bot")
            for i in range(num_players)
        ]
        table = Table(players=players)
        strategy = PlaceholderStrategy()
        strategies = {f"Bot-{i}": strategy for i in range(num_players)}
        return GameEngine(
            table=table,
            strategies=strategies,
            rng=random.Random(42),
        )

    def test_one_hand_completes(self) -> None:
        engine = self._make_engine(3)
        engine.play_hand()
        assert engine.hand_over

    def test_hand_number_increments(self) -> None:
        engine = self._make_engine(3)
        engine.play_hand()
        assert engine.state.hand_number == 1
        engine.init_new_hand()
        assert engine.state.hand_number == 2

    def test_pot_has_money_after_hand(self) -> None:
        engine = self._make_engine(3)
        engine.play_hand()
        assert engine.state.pot.total > 0

    def test_players_get_hole_cards(self) -> None:
        engine = self._make_engine(3)
        engine.init_new_hand()
        for p in engine.state.table.players:
            if not p.is_out:
                assert len(p.hand.cards) == 2

    def test_blinds_are_posted(self) -> None:
        engine = self._make_engine(3)
        engine.init_new_hand()
        blinds_total = 30
        assert engine.state.pot.total >= blinds_total

    def test_winner_gets_pot(self) -> None:
        engine = self._make_engine(2)
        stacks_before = {p.name: p.stack for p in engine.state.table.players}
        engine.play_hand()
        total_stacks = sum(p.stack for p in engine.state.table.players)
        total_before = sum(stacks_before.values())
        assert total_stacks == total_before

    def test_folded_player_cannot_act(self) -> None:
        engine = self._make_engine(3)
        engine.init_new_hand()
        for p in engine.state.table.players:
            p.status = PlayerStatus.FOLDED
        legal = engine.get_legal_actions_for_current()
        assert len(legal) == 0

    def test_many_hands_complete(self) -> None:
        engine = self._make_engine(4)
        for _ in range(10):
            engine.play_hand()
            assert engine.hand_over
            remaining = [p for p in engine.state.table.players if not p.is_out]
            if len(remaining) <= 1:
                for p in engine.state.table.players:
                    p.status = PlayerStatus.ACTIVE
                    p.stack = 1000
                    p.reset_for_new_hand()
