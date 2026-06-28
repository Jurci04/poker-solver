from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Footer, Header, Static

from poker_tui.domain.enums import PlayerStatus
from poker_tui.engine.events import HandEnded, PlayerActed
from poker_tui.simulation.runner import SimulationRunner
from poker_tui.tui.apps.table_render import board, players_grid, update_static


class ObserveApp(App[None]):
    CSS = """
    Screen { layout: vertical; }
    #status { height: 1; padding: 0 1; }
    #board { height: 7; border: solid green; content-align: center middle; }
    #table { height: 1fr; border: solid green; padding: 1 2; overflow-y: auto; }
    #log { height: 6; border: solid gray; padding: 0 1; overflow-y: auto; }
    #controls { height: 3; padding: 0 1; }
    Button { margin-right: 1; }
    """

    def __init__(self, runner: SimulationRunner, num_hands: int) -> None:
        super().__init__()
        self._runner = runner
        self._num_hands = num_hands
        self._engine = runner.engine
        self._paused = False
        self._done = False
        self._waiting_continue = False
        self._speed = 1.0
        self._hands_completed = 0
        self._last_actions: dict[str, str] = {}
        self._lines: list[str] = []
        self._timer = None
        self._last_render: dict[str, str] = {}
        self._winners: set[str] = set()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Starting...", id="status")
        yield Static("Board: --", id="board")
        yield Static("Dealing...", id="table")
        yield Static("", id="log")
        with Horizontal(id="controls"):
            yield Button("Pause", id="pause", variant="primary")
            yield Button("Step", id="step", variant="warning")
            yield Button("Continue", id="continue", variant="success", disabled=True)
            yield Button("Slower", id="slower")
            yield Button("Faster", id="faster")
            yield Button("Quit", id="quit", variant="error")
        yield Footer()

    def on_mount(self) -> None:
        self._engine.event_bus.subscribe("player_acted", self._on_player_acted)
        self._engine.event_bus.subscribe("hand_ended", self._on_hand_ended)
        self._start_hand()
        self._timer = self.set_interval(0.1, self._tick)

    def _on_player_acted(self, event: object) -> None:
        if isinstance(event, PlayerActed):
            self._last_actions[event.player_name] = str(event.action)

    def _on_hand_ended(self, event: object) -> None:
        if not isinstance(event, HandEnded):
            return
        self._hands_completed += 1
        self._winners = {winner["name"] for winner in event.winners}
        names = ", ".join(f'{w["name"]} +${w["amount"]}' for w in event.winners)
        self._add_log(f"Winner: {names}")
        if sum(1 for p in self._engine.state.table.players if not p.is_out) <= 1:
            for player in self._engine.state.table.players:
                player.status = PlayerStatus.ACTIVE
                player.stack = 1000

    def _tick(self) -> None:
        if self._paused or self._done:
            return
        self._step()

    def _step(self) -> None:
        if self._waiting_continue:
            return
        if self._engine.hand_over:
            if self._hands_completed >= self._num_hands:
                self._done = True
                self._add_log("Simulation complete")
            else:
                self._waiting_continue = True
                self.query_one("#continue", Button).disabled = False
            self._render()
            return
        self._engine.step()
        self._render()

    def _start_hand(self) -> None:
        self._waiting_continue = False
        self.query_one("#continue", Button).disabled = True
        self._engine.init_new_hand()
        self._last_actions.clear()
        self._winners.clear()
        self._add_log(f"Hand {self._engine.state.hand_number}")
        self._render()

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
            f"Hand {self._hands_completed}/{self._num_hands} | "
            f"{state.street.value.upper()} | Pot ${state.pot.total} | "
            f"Active {active}/{total} | Speed {self._speed}x",
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
            players_grid(
                table.players,
                current,
                self._winners,
                self._last_actions,
                {p.name: True for p in table.players},
            ),
        )
        update_static(self, self._last_render, "#log", "\n".join(self._lines[-6:]))

    def _add_log(self, line: str) -> None:
        self._lines.append(line)
        self._lines = self._lines[-50:]

    def _reset_timer(self) -> None:
        if self._timer:
            self._timer.stop()
        self._timer = self.set_interval(max(0.02, 0.1 / self._speed), self._tick)

    @on(Button.Pressed)
    def on_button(self, event: Button.Pressed) -> None:
        if event.button.id == "pause":
            self._paused = not self._paused
            event.button.label = "Resume" if self._paused else "Pause"
        elif event.button.id == "continue" and self._waiting_continue:
            self._start_hand()
        elif event.button.id == "step" and not self._done:
            self._step()
        elif event.button.id == "slower":
            self._speed = max(0.25, self._speed / 2)
            self._reset_timer()
            self._render()
        elif event.button.id == "faster":
            self._speed = min(8.0, self._speed * 2)
            self._reset_timer()
            self._render()
        elif event.button.id == "quit":
            self.exit()
