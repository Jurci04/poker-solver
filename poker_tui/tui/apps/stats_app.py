from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Static

from poker_tui.simulation.result import SimulationResult


class StatsApp(App[None]):
    CSS = """
    Screen { layout: grid; grid-size: 2 2; }
    Static { border: solid green; padding: 1; }
    """

    def __init__(self, result: SimulationResult) -> None:
        super().__init__()
        self._result = result

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(Static(id="summary"), Static(id="profit"))
        yield Container(Static(id="winrate"), Static(id="actions"))
        yield Footer()

    def on_mount(self) -> None:
        stats = self._result.player_stats
        self.query_one("#summary", Static).update(self._summary(stats))
        self.query_one("#profit", Static).update(self._bars("Profit", stats, "profit", money=True))
        self.query_one("#winrate", Static).update(self._bars("Win Rate", stats, "win_rate"))
        self.query_one("#actions", Static).update(self._actions())

    def _summary(self, stats: dict[str, dict[str, Any]]) -> str:
        lines = ["[bold]Session Stats[/]"]
        for name, row in stats.items():
            lines.append(
                f"{name}: {row.get('wins', 0)} wins "
                f"({row.get('win_rate', 0):.1%}), ${row.get('profit', 0):+d}"
            )
        return "\n".join(lines)

    def _bars(
        self,
        title: str,
        stats: dict[str, dict[str, Any]],
        key: str,
        money: bool = False,
    ) -> str:
        values = {name: float(row.get(key, 0)) for name, row in stats.items()}
        scale = max((abs(v) for v in values.values()), default=1) or 1
        lines = [f"[bold]{title}[/]"]
        for name, value in values.items():
            bar = "#" * int(abs(value) / scale * 30)
            color = "green" if value >= 0 else "red"
            label = f"${value:+.0f}" if money else f"{value:.1%}"
            lines.append(f"{name}: [{color}]{bar}[/] {label}")
        return "\n".join(lines)

    def _actions(self) -> str:
        lines = ["[bold]Actions[/]"]
        for name, actions in self._result.action_frequencies.items():
            total = sum(actions.values())
            if total:
                parts = [f"{a}:{c}" for a, c in sorted(actions.items())]
                lines.append(f"{name}: {', '.join(parts)}")
        return "\n".join(lines)
