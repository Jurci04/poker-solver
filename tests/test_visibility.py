from poker_tui.domain.card import Card
from poker_tui.domain.enums import Rank, Street, Suit
from poker_tui.domain.player import Player
from poker_tui.domain.table import Table
from poker_tui.engine.visibility import VisibilityFilter


class TestVisibility:
    def _make_table(self) -> Table:
        alice = Player(name="Alice", stack=1000, position=0)
        bob = Player(name="Bob", stack=1000, position=1)
        alice.hand.add_card(Card(Rank.ACE, Suit.HEARTS))
        alice.hand.add_card(Card(Rank.KING, Suit.HEARTS))
        bob.hand.add_card(Card(Rank.TWO, Suit.CLUBS))
        bob.hand.add_card(Card(Rank.THREE, Suit.CLUBS))
        return Table(players=[alice, bob])

    def test_public_state_hides_all_cards_by_default(self) -> None:
        table = self._make_table()
        state = VisibilityFilter.public_state(
            table=table, pot_total=100, current_bet=0,
            street=Street.FLOP, hand_number=1,
            current_player_name="Alice",
        )
        for p in state.players:
            assert len(p.hole_cards) == 0

    def test_public_state_shows_all_with_flag(self) -> None:
        table = self._make_table()
        state = VisibilityFilter.public_state(
            table=table, pot_total=100, current_bet=0,
            street=Street.FLOP, hand_number=1,
            current_player_name="Alice",
            show_all=True,
        )
        for p in state.players:
            assert len(p.hole_cards) == 2

    def test_player_state_shows_own_cards(self) -> None:
        table = self._make_table()
        alice = table.players[0]
        state = VisibilityFilter.player_state(
            table=table, player=alice, pot_total=100, current_bet=0,
            street=Street.FLOP, hand_number=1, legal_actions=[],
        )
        alice_view = state.get_player_view("Alice")
        assert alice_view is not None
        assert len(alice_view.hole_cards) == 2

    def test_player_state_hides_opponent_cards(self) -> None:
        table = self._make_table()
        alice = table.players[0]
        state = VisibilityFilter.player_state(
            table=table, player=alice, pot_total=100, current_bet=0,
            street=Street.FLOP, hand_number=1, legal_actions=[],
        )
        bob_view = state.get_player_view("Bob")
        assert bob_view is not None
        assert len(bob_view.hole_cards) == 0

    def test_show_opponent_cards_flag(self) -> None:
        table = self._make_table()
        alice = table.players[0]
        state = VisibilityFilter.player_state(
            table=table, player=alice, pot_total=100, current_bet=0,
            street=Street.FLOP, hand_number=1, legal_actions=[],
            show_opponent_cards=True,
        )
        bob_view = state.get_player_view("Bob")
        assert bob_view is not None
        assert len(bob_view.hole_cards) == 2

    def test_strategy_only_gets_player_state_view(self) -> None:
        table = self._make_table()
        alice = table.players[0]
        state = VisibilityFilter.player_state(
            table=table, player=alice, pot_total=100, current_bet=0,
            street=Street.FLOP, hand_number=1, legal_actions=[],
        )
        assert len(state.players) == 2
        bob_view = state.get_player_view("Bob")
        assert bob_view is not None
        assert len(bob_view.hole_cards) == 0

    def test_player_state_at_showdown_reveals_all(self) -> None:
        table = self._make_table()
        alice = table.players[0]
        state = VisibilityFilter.player_state(
            table=table, player=alice, pot_total=100, current_bet=0,
            street=Street.SHOWDOWN, hand_number=1, legal_actions=[],
        )
        bob_view = state.get_player_view("Bob")
        assert bob_view is not None
        assert len(bob_view.hole_cards) == 2
