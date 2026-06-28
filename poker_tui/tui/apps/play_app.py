from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Footer, Header, Label

from poker_tui.domain.action import Action
from poker_tui.domain.enums import ActionType, Street
from poker_tui.engine.events import HandEnded
from poker_tui.engine.game_engine import GameEngine
from poker_tui.tui.widgets.action_log_widget import ActionLogWidget
from poker_tui.tui.widgets.action_panel_widget import ActionPanelWidget
from poker_tui.tui.widgets.table_widget import TableWidget


class PlayApp(App[None]):
    """Textual UI for human play against bots."""

    CSS = """
    Screen { layout: grid; grid-size: 3 3; grid-rows: auto 4fr 1fr; }
    #info-container { border: solid $primary; padding: 1 2; column-span: 3; height: auto; }
    #table-container { border: solid $primary; padding: 1 2; column-span: 2; }
    #log-container { border: solid $secondary; padding: 1; overflow-y: auto; }
    #action-container { border: solid $accent; padding: 1; column-span: 3; }
    #opponent-seats { layout: horizontal; height: auto; margin-bottom: 1; }
    #opponent-seats > PlayerSeatWidget { margin: 0 1; min-width: 14; }
    .hidden { display: none; }
    """

    def __init__(self, engine: GameEngine, show_all: bool = False) -> None:
        self._engine = engine
        self._table: TableWidget = TableWidget(engine, show_all)
        self._log_widget: ActionLogWidget = ActionLogWidget()
        self._panel: ActionPanelWidget = ActionPanelWidget()
        self._last_street: Street = Street.PREFLOP
        self._result: dict[str, Any] | None = None
        self._pending_next: int = 0
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="info-container"):
            yield Label(id="game-info")
        with Container(id="table-container"):
            yield self._table
        with Container(id="log-container"):
            yield self._log_widget
        with Container(id="action-container"):
            yield self._panel
        yield Footer()

    def on_mount(self) -> None:
        self._engine.event_bus.subscribe("hand_ended", self._on_hand_ended)
        self._start_new_hand()
        self.set_interval(0.05, self._tick)
        self._refresh()

    def _on_hand_ended(self, event: object) -> None:
        if not isinstance(event, HandEnded):
            return
        self._result = {
            "winners": event.winners,
            "pot": event.pot_amount,
            "hand": event.hand_number,
        }
        names = ", ".join(f'{w["name"]} (${w["amount"]})' for w in event.winners)
        tag = "Winner" if len(event.winners) == 1 else "Winners"
        self._log_widget.add_line(f"{tag}: {names}")

    def _tick(self) -> None:
        if self._engine.hand_over:
            if self._result:
                self._show_hand_result()
            elif self._pending_next > 0:
                self._pending_next -= 1
                if self._pending_next == 0:
                    self._start_new_hand()
            self._refresh()
        elif self._engine.waiting_for_human:
            self._panel.set_legal_actions(self._engine.get_legal_actions_for_current())
            self._refresh()
        else:
            self._engine.step()
            self._check_street()
            self._refresh()

    def _show_hand_result(self) -> None:
        r = self._result
        if not r:
            return
        human = next((p for p in self._engine.state.table.players if p.name == "You"), None)
        if human and human.stack <= 0:
            self._panel.show_result(
                "[bold red]You're busted![/]\nGame over — close the window or press Ctrl+C"
            )
            self._result = None
            return
        lines = ["[bold]Hand Over[/]"]
        for w in r["winners"]:
            lines.append(f"  {w['name']} won ${w['amount']}")
        self._panel.show_result("\n".join(lines))
        self._result = None
        self._pending_next = 10

    def _check_street(self) -> None:
        s = self._engine.state.street
        if s != self._last_street:
            self._last_street = s
            label = {Street.PREFLOP: "Preflop", Street.FLOP: "Flop", Street.TURN: "Turn",
                     Street.RIVER: "River", Street.SHOWDOWN: "Showdown"}.get(s)
            if label:
                self._log_widget.add_line(f"--- {label} ---")

    def _refresh(self) -> None:
        self._table.refresh_display()
        info = self._build_game_info()
        self.query_one("#game-info", Label).update(info)

    def _build_game_info(self) -> str:
        state = self._engine.state
        table = state.table
        total = state.pot.total
        street_str = state.street.value.upper()
        hand = state.hand_number
        dealer = table.players[table.dealer_position].name
        active = sum(1 for p in table.players if not p.is_folded and not p.is_out)
        total_in = sum(1 for p in table.players if not p.is_out)
        return (
            f"[bold]#{hand}[/] | {street_str} | "
            f"[yellow]Pot: ${total}[/] | "
            f"Players: {active}/{total_in} | "
            f"[dim]Dealer: {dealer}[/]"
        )

    def _start_new_hand(self) -> None:
        self._result = None
        self._pending_next = 0
        self._engine.init_new_hand()
        self._log_widget.add_line(f"\n--- Hand {self._engine.state.hand_number} ---")
        self._last_street = self._engine.state.street
        self._panel.disable_all()
        self._refresh()

    @on(Button.Pressed)
    def on_button(self, event: Button.Pressed) -> None:
        if event.button.id == "next_hand":
            self._start_new_hand()
            return
        if not self._engine.waiting_for_human:
            return
        player = self._engine.get_current_player()
        if player is None:
            return

        btn_map = {"fold": ActionType.FOLD, "check": ActionType.CHECK,
                   "call": ActionType.CALL, "bet": ActionType.BET, "raise": ActionType.RAISE}
        atype = btn_map.get(event.button.id or "")
        if atype is None:
            return

        legal = self._engine.get_legal_actions_for_current()
        if atype in (ActionType.BET, ActionType.RAISE):
            amount_str = self._panel.get_amount()
            try:
                amount = int(amount_str)
            except (ValueError, TypeError):
                return
            if amount <= 0:
                return
            action = Action(atype, amount)
        else:
            match = [a for a in legal if a.action_type == atype]
            if not match:
                return
            action = match[0]

        self._log_widget.add_line(f"You: {action}")
        self._engine.handle_human_action(player, action)
        self._panel.disable_all()
        self._engine.advance_to_next_player()
        self._refresh()

