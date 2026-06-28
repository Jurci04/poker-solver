from textual.widgets import Static

from poker_tui.domain.card import Card
from poker_tui.tui.widgets.card_render import card_boxes


class CommunityCardsWidget(Static):
    """Displays community cards with suit coloring."""

    def update_cards(self, cards: list[Card]) -> None:
        if not cards:
            self.update("[dim]Board: --[/]")
            return
        self.update(f"[bold]Board:[/]\n{card_boxes(cards)}")
