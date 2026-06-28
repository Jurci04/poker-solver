from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Footer, Header, Label

from poker_tui.simulation.runner import SimulationRunner
from poker_tui.tui.widgets.action_log_widget import ActionLogWidget
from poker_tui.tui.widgets.table_widget import TableWidget


class ObserveApp(App[None]):
    """Textual observer for bot-vs-bot games with pause/step/speed controls."""

    CSS = """
    Screen { layout: grid; grid-size: 2 2; grid-rows: 3fr 1fr; }
    #table-container { border: solid $primary; padding: 1; }
    #log-container { border: solid $secondary; padding: 1; overflow-y: auto; }
    #controls { border: solid $accent; padding: 1; column-span: 2; height: auto; }
    #progress-label { padding: 0 1; }
    Button { margin: 0 1; }
    """

    def __init__(self, runner: SimulationRunner, num_hands: int, show_all: bool = False) -> None:
        super().__init__()
        self._runner = runner
        self._num_hands = num_hands
        self._engine = runner.engine
        self._paused = False
        self._speed = 1.0
        self._table = TableWidget(self._engine, show_all)
        self._log_widget: ActionLogWidget = ActionLogWidget()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="table-container"):
            yield Label(id="progress-label")
            yield self._table
        with Container(id="log-container"):
            yield self._log_widget
        with Container(id="controls"):
            with Horizontal():
                yield Button("Pause", id="pause", variant="primary")
                yield Button("Step", id="step", variant="warning")
                yield Button("Slower", id="slower")
                yield Button("Faster", id="faster")
                yield Button("Quit", id="quit", variant="error")
        yield Footer()

    def on_mount(self) -> None:
        self._engine.init_new_hand()
        self._log_widget.add_line(f"--- Hand {self._engine.state.hand_number} ---")
        self._update_timer()

    def _update_timer(self) -> None:
        try:
            self.set_interval(max(0.01, 0.1 / self._speed), self._tick)
        except Exception:
            pass

    def _tick(self) -> None:
        if self._paused:
            return
        if self._engine.hand_over:
            self._next_hand()
        else:
            self._engine.step()
            self._refresh()

    def _next_hand(self) -> None:
        if self._runner.stats.hands_completed >= self._num_hands:
            self._log_widget.add_line("--- Simulation complete ---")
            return
        self._runner.run_step()
        self._log_widget.add_line(f"--- Hand {self._engine.state.hand_number} ---")
        self._refresh()

    def _refresh(self) -> None:
        self._table.refresh_display()
        self.query_one("#progress-label", Label).update(
            f"Hand {self._runner.stats.hands_completed}/{self._num_hands} | Speed: {self._speed}x"
        )

    @on(Button.Pressed)
    def on_button(self, event: Button.Pressed) -> None:
        btn = event.button.id
        if btn == "pause":
            self._paused = not self._paused
            event.button.label = "Resume" if self._paused else "Pause"
        elif btn == "step":
            if self._engine.hand_over:
                self._next_hand()
            else:
                self._engine.step()
                self._refresh()
        elif btn == "slower":
            self._speed = max(0.25, self._speed / 2)
            self._refresh()
        elif btn == "faster":
            self._speed = min(8.0, self._speed * 2)
            self._refresh()
        elif btn == "quit":
            self.exit()
