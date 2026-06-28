from textual.widgets import Static


class PotWidget(Static):
    """Displays the current pot total and current bet."""

    def update_pot(self, total: int, current_bet: int = 0) -> None:
        parts = [f"[bold yellow]Pot: ${total}[/]"]
        if current_bet > 0:
            parts.append(f"[dim]Current bet: ${current_bet}[/]")
        self.update("  ".join(parts))
