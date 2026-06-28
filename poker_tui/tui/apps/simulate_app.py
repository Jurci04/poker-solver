from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Label, ProgressBar

from poker_tui.simulation.result import SimulationResult
from poker_tui.simulation.runner import SimulationRunner


class SimulateApp(App[SimulationResult]):
    """Simple progress bar while simulation runs, then exits.
    *run_all* is called on mount; the screen blocks until all hands finish."""

    CSS = """
    Screen { align: center middle; }
    #status { padding: 1 2; }
    ProgressBar { width: 60; }
    """

    def __init__(self, runner: SimulationRunner, num_hands: int) -> None:
        super().__init__()
        self._runner = runner
        self._num_hands = num_hands
        self._progress = ProgressBar(total=num_hands)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("Running simulation...", id="status"),
            self._progress,
        )
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(0.1, self._tick)
        self._runner.run_all()

    def _tick(self) -> None:
        done = self._runner.stats.hands_completed
        self._progress.update(progress=done)
        if done >= self._num_hands:
            self.exit(self._runner.stats.get_result())
