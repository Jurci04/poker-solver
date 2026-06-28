from typing import Any

from textual.widgets import Static


class StatsWidget(Static):
    """Displays session-level player stats in a compact format."""

    def update_stats(self, player_stats: dict[str, Any]) -> None:
        lines = ["[bold]Session Stats[/]"]
        for name, s in player_stats.items():
            lines.append(
                f"  {name}: {s.get('wins', 0)} wins ({s.get('win_rate', 0):.1%}), "
                f"${s.get('profit', 0):+d}"
            )
        self.update("\n".join(lines))
