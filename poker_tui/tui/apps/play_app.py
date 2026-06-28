from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Footer, Header, Input, Static

from poker_tui.domain.action import Action
from poker_tui.domain.enums import ActionType, Street
from poker_tui.engine.events import HandEnded, PlayerActed
from poker_tui.engine.game_engine import GameEngine
from poker_tui.tui.apps.table_render import board, player_block, update_static


class PlayApp(App[None]):
    CSS = """
    Screen { layout: vertical; }
    #status { height: 1; padding: 0 1; }
    #board { height: 4; border: solid green; content-align: center middle; }
    #table { height: 1fr; border: solid green; padding: 1 2; }
    #log { height: 6; border: solid gray; padding: 0 1; overflow-y: auto; }
    #actions { height: 3; padding: 0 1; }
    Button { margin-right: 1; }
    #amount { width: 12; }
    """

    def __init__(self, engine: GameEngine, show_all: bool = False) -> None:
        super().__init__()
        self._engine = engine
        self._show_all = show_all
        self._last_street = Street.PREFLOP
        self._last_actions: dict[str, str] = {}
        self._lines: list[str] = []
        self._result: dict[str, Any] | None = None
        self._last_render: dict[str, str] = {}
        self._winners: set[str] = set()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Starting...", id="status")
        yield Static("Board: --", id="board")
        yield Static("Dealing...", id="table")
        yield Static("", id="log")
        with Horizontal(id="actions"):
            yield Button("Fold", id="fold", variant="error", disabled=True)
            yield Button("Check", id="check", disabled=True)
            yield Button("Call", id="call", disabled=True)
            yield Button("Bet", id="bet", variant="warning", disabled=True)
            yield Button("Raise", id="raise", variant="warning", disabled=True)
            yield Input(placeholder="Amount", id="amount", type="integer", disabled=True)
            yield Button("New Hand", id="new_hand", variant="success", disabled=True)
        yield Footer()

    def on_mount(self) -> None:
        self._engine.event_bus.subscribe("hand_ended", self._on_hand_ended)
        self._engine.event_bus.subscribe("player_acted", self._on_player_acted)
        self._start_hand()
        self.set_interval(0.1, self._tick)

    def _on_player_acted(self, event: object) -> None:
        if isinstance(event, PlayerActed):
            self._last_actions[event.player_name] = str(event.action)

    def _on_hand_ended(self, event: object) -> None:
        if isinstance(event, HandEnded):
            self._result = {"winners": event.winners, "pot": event.pot_amount}
            names = ", ".join(f'{w["name"]} +${w["amount"]}' for w in event.winners)
            self._add_log(f"Winner: {names}")

    def _tick(self) -> None:
        if self._engine.hand_over:
            if self._result:
                self._show_result()
            self._render()
            return

        if self._engine.waiting_for_human:
            self._set_actions()
            self._render()
            return

        self._engine.step()
        self._check_street()
        self._render()

    def _start_hand(self) -> None:
        self._result = None
        self._last_actions.clear()
        self._winners.clear()
        self._engine.init_new_hand()
        self._last_street = self._engine.state.street
        self._add_log(f"Hand {self._engine.state.hand_number}")
        self._disable_actions()
        self.query_one("#new_hand", Button).disabled = True
        self._render()

    def _check_street(self) -> None:
        street = self._engine.state.street
        if street != self._last_street:
            self._last_street = street
            self._last_actions.clear()
            self._add_log(street.value.upper())

    def _show_result(self) -> None:
        result = self._result
        if result is None:
            return
        self._disable_actions()
        self._winners = {winner["name"] for winner in result["winners"]}
        for winner in result["winners"]:
            self._add_log(f'{winner["name"]} won ${winner["amount"]}')
        self._result = None
        self.query_one("#new_hand", Button).disabled = False

    def _render(self) -> None:
        state = self._engine.state
        table = state.table
        current = self._engine.get_current_player()
        active = sum(1 for p in table.players if not p.is_folded and not p.is_out)
        total = sum(1 for p in table.players if not p.is_out)

        update_static(
            self,
            self._last_render,
            "#status",
            f"Hand {state.hand_number} | {state.street.value.upper()} | "
            f"Pot ${state.pot.total} | Active {active}/{total}",
        )
        update_static(
            self,
            self._last_render,
            "#board",
            board(table.community_cards),
        )
        update_static(
            self,
            self._last_render,
            "#table",
            "\n".join(
                player_block(
                    p,
                    current,
                    self._winners,
                    self._last_actions,
                    self._show_all
                    or p.name == "You"
                    or (state.street == Street.SHOWDOWN and not p.is_folded),
                )
                for p in table.players
            ),
        )
        update_static(self, self._last_render, "#log", "\n".join(self._lines[-6:]))

    def _add_log(self, line: str) -> None:
        self._lines.append(line)
        self._lines = self._lines[-50:]

    def _set_actions(self) -> None:
        legal = {action.action_type for action in self._engine.get_legal_actions_for_current()}
        for action_type, button_id in {
            ActionType.FOLD: "fold",
            ActionType.CHECK: "check",
            ActionType.CALL: "call",
            ActionType.BET: "bet",
            ActionType.RAISE: "raise",
        }.items():
            self.query_one(f"#{button_id}", Button).disabled = action_type not in legal
        self.query_one("#amount", Input).disabled = not (
            ActionType.BET in legal or ActionType.RAISE in legal
        )

    def _disable_actions(self) -> None:
        for button_id in ("fold", "check", "call", "bet", "raise"):
            self.query_one(f"#{button_id}", Button).disabled = True
        self.query_one("#amount", Input).disabled = True

    @on(Button.Pressed)
    def on_button(self, event: Button.Pressed) -> None:
        if event.button.id == "new_hand":
            if self._engine.hand_over:
                self._start_hand()
            return

        if not self._engine.waiting_for_human:
            return

        action_type = {
            "fold": ActionType.FOLD,
            "check": ActionType.CHECK,
            "call": ActionType.CALL,
            "bet": ActionType.BET,
            "raise": ActionType.RAISE,
        }.get(event.button.id or "")
        player = self._engine.get_current_player()
        if action_type is None or player is None:
            return

        legal = self._engine.get_legal_actions_for_current()
        if action_type in (ActionType.BET, ActionType.RAISE):
            amount = int(self.query_one("#amount", Input).value or "0")
            if amount <= 0:
                return
            action = Action(action_type, amount)
        else:
            action = next((a for a in legal if a.action_type == action_type), None)
            if action is None:
                return

        self._last_actions[player.name] = str(action)
        self._engine.handle_human_action(player, action)
        self._engine.advance_to_next_player()
        self._disable_actions()
        self._render()
