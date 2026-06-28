from poker_tui.domain.action import Action
from poker_tui.domain.enums import ActionType, PlayerStatus
from poker_tui.domain.player import Player
from poker_tui.domain.table import Table
from poker_tui.engine.betting import BettingRound, get_legal_actions


class TestBetting:
    def _make_table(self) -> Table:
        players = [
            Player(name="Alice", stack=1000, position=0),
            Player(name="Bob", stack=1000, position=1),
        ]
        return Table(players=players)

    def test_legal_actions_include_fold(self) -> None:
        table = self._make_table()
        player = table.players[0]
        actions = get_legal_actions(player, table)
        assert any(a.action_type == ActionType.FOLD for a in actions)

    def test_legal_actions_include_check_when_no_bet(self) -> None:
        table = self._make_table()
        player = table.players[0]
        actions = get_legal_actions(player, table)
        assert any(a.action_type == ActionType.CHECK for a in actions)

    def test_legal_actions_include_call_when_bet_exists(self) -> None:
        table = self._make_table()
        table.players[1].current_bet = 20
        player = table.players[0]
        actions = get_legal_actions(player, table)
        assert any(a.action_type == ActionType.CALL for a in actions)

    def test_folded_player_has_no_actions(self) -> None:
        table = self._make_table()
        player = table.players[0]
        player.status = PlayerStatus.FOLDED
        actions = get_legal_actions(player, table)
        assert len(actions) == 0

    def test_betting_updates_stack(self) -> None:
        table = self._make_table()
        player = table.players[0]
        round = BettingRound(table)
        round.process_action(player, Action.bet(20))
        assert player.stack == 980
        assert player.current_bet == 20

    def test_fold_changes_status(self) -> None:
        table = self._make_table()
        player = table.players[0]
        round = BettingRound(table)
        round.process_action(player, Action.fold())
        assert player.is_folded

    def test_call_matches_bet(self) -> None:
        table = self._make_table()
        table.players[0].current_bet = 20
        table.players[1].current_bet = 0
        round = BettingRound(table)
        round.process_action(table.players[1], Action.call(20))
        assert table.players[1].current_bet == 20
        assert table.players[1].stack == 980

    def test_raise_increases_bet(self) -> None:
        table = self._make_table()
        table.players[0].post_bet(10)
        table.players[1].post_bet(10)
        round = BettingRound(table)
        round.process_action(table.players[1], Action.raise_(30))
        assert table.players[1].current_bet == 30
        assert table.players[1].stack == 960
