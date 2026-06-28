from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Label

from poker_tui.simulation.result import SimulationResult
from poker_tui.tui.widgets.chart_widget import ChartWidget
from poker_tui.tui.widgets.stats_widget import StatsWidget


class StatsApp(App[None]):
    """Displays simulation statistics with charts and a summary table."""

    CSS = """
    Screen { layout: grid; grid-size: 2 2; }
    #summary-container { border: solid $primary; padding: 1; }
    #profit-container { border: solid $secondary; padding: 1; }
    #winrate-container { border: solid $accent; padding: 1; }
    #sparkline-container { border: solid $accent; padding: 1; }
    """

    def __init__(self, result: SimulationResult) -> None:
        super().__init__()
        self._result = result

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="summary-container"):
            yield StatsWidget(id="summary")
        with Container(id="profit-container"):
            yield Label("[bold]Profit[/]")
            yield ChartWidget(id="profit-chart")
        with Container(id="winrate-container"):
            yield Label("[bold]Win Rate[/]")
            yield ChartWidget(id="winrate-chart")
        with Container(id="sparkline-container"):
            yield Label("[bold]Profit History[/]")
            yield ChartWidget(id="sparkline")
        yield Footer()

    def on_mount(self) -> None:
        result = self._result

        self.query_one("#summary", StatsWidget).update_stats(result.player_stats)

        profits = {p: result.player_stats[p]["profit"]
                   for p in result.player_stats}
        self.query_one("#profit-chart", ChartWidget).show_horizontal_bars(
            profits, max_width=40
        )

        rates = {p: result.player_stats[p]["win_rate"]
                 for p in result.player_stats}
        self.query_one("#winrate-chart", ChartWidget).show_percentage_bars(
            rates, max_width=40
        )
