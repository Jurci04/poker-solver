from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from poker_tui.engine.game_engine import GameEngine
from poker_tui.engine.public_state import PlayerView
from poker_tui.tui.widgets.community_cards_widget import CommunityCardsWidget
from poker_tui.tui.widgets.player_seat_widget import PlayerSeatWidget
from poker_tui.tui.widgets.pot_widget import PotWidget


class TableWidget(Static):
    """Table-centric layout: opponents across the top, community cards + pot
    in the center, and the human player's seat at the bottom."""

    def __init__(self, engine: GameEngine, show_all: bool = False) -> None:
        super().__init__()
        self._engine = engine
        self._show_all = show_all
        self._seats: dict[str, PlayerSeatWidget] = {}
        self._pot = PotWidget()
        self._community = CommunityCardsWidget()

    def compose(self) -> ComposeResult:
        table = self._engine.state.table
        has_human = any(p.name == "You" for p in table.players)
        with Horizontal(id="opponent-seats"):
            for p in table.players:
                if has_human and p.name == "You":
                    continue
                if p.is_out:
                    continue
                sw = PlayerSeatWidget(id=f"seat-{p.name}")
                self._seats[p.name] = sw
                yield sw
        yield self._community
        yield self._pot
        if has_human:
            human = next((p for p in table.players if p.name == "You"), None)
            if human and not human.is_out:
                sw = PlayerSeatWidget(id="seat-You")
                self._seats["You"] = sw
                yield sw

    def refresh_display(self) -> None:
        table = self._engine.state.table
        street = self._engine.state.street
        self._community.update_cards(table.community_cards)
        pot = self._engine.state.pot
        self._pot.update_pot(pot.total, pot.current_bet)

        current = self._engine.get_current_player()
        current_name = current.name if current else None

        for p in table.players:
            sw = self._seats.get(p.name)
            if sw is None:
                continue

            show_cards = self._show_all or p.name == "You" or (
                street.name == "SHOWDOWN" and not p.is_folded and not p.is_out
            )
            hole = list(p.hand.cards) if show_cards else []

            sw.update_player(PlayerView(
                name=p.name, stack=p.stack, position=p.position,
                current_bet=p.current_bet, is_dealer=p.is_dealer,
                is_small_blind=p.is_small_blind, is_big_blind=p.is_big_blind,
                is_active=p.is_active, is_folded=p.is_folded,
                hole_cards=hole,
            ), compact=p.name != "You")
            sw.styles.background = "green" if p.name == current_name else ""
