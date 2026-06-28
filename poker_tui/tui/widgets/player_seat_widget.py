from textual.widgets import Static

from poker_tui.engine.public_state import PlayerView
from poker_tui.tui.widgets.card_render import card_boxes

_ACTION_STYLES = {
    "fold": "[red]FOLD[/]",
    "check": "[cyan]CHECK[/]",
    "call": "[green]CALL[/]",
    "bet": "[yellow]BET[/]",
    "raise": "[magenta]RAISE[/]",
    "all_in": "[bold red]ALL-IN[/]",
}


class PlayerSeatWidget(Static):
    """Displays a player's name, stack, position markers, and hole cards.

    Two display modes:
      - compact (opponents): one/two-line summary
      - full (human): card boxes + full info
    """

    def update_player(
        self, player: PlayerView, compact: bool = False, last_action: str | None = None
    ) -> None:
        markers = ""
        if player.is_dealer:
            markers += " D"
        if player.is_small_blind:
            markers += " SB"
        if player.is_big_blind:
            markers += " BB"

        status = " [dim](folded)[/]" if player.is_folded else ""
        name_style = "[bold green]" if player.is_active else "[dim]"

        action_line = ""
        if last_action:
            style = _ACTION_STYLES.get(last_action.split()[0].lower(), "bold white")
            action_line = f"\n  {style}[/]"

        if compact:
            self.update(
                f"{name_style}{player.name}[/]{markers}{status}{action_line}\n"
                f"  [dim]${player.stack}:{player.current_bet}[/]"
            )
        else:
            body = f"{name_style}{player.name}[/]{markers}{status}"
            if player.hole_cards:
                body += "\n" + card_boxes(player.hole_cards)
            body += action_line
            body += f"\n  Stack: ${player.stack}  Bet: ${player.current_bet}"
            if player.is_active and not player.is_folded:
                body += "\n[bold yellow]◄ YOUR HAND[/]"
            self.update(body)
