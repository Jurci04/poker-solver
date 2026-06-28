from typing import Any

from textual.app import App
from textual.widgets import Static

from poker_tui.domain.card import Card
from poker_tui.domain.player import Player

INFO_WIDTH = 52


def update_static(app: App[Any], cache: dict[str, str], selector: str, text: str) -> None:
    if cache.get(selector) != text:
        cache[selector] = text
        app.query_one(selector, Static).update(text)


def board(cards: list[Card]) -> str:
    if not cards:
        return "Board: [--]"
    rows = card_rows(cards)
    return "\n".join((f"Board  {rows[0]}", f"       {rows[1]}", f"       {rows[2]}"))


def player_block(
    player: Player,
    current: Player | None,
    winners: set[str],
    last_actions: dict[str, str],
    show_cards: bool,
) -> str:
    marks = []
    if player.is_dealer:
        marks.append("D")
    if player.is_small_blind:
        marks.append("SB")
    if player.is_big_blind:
        marks.append("BB")
    if player == current:
        marks.append("TURN")
    if player.is_folded:
        marks.append("FOLDED")

    winner = player.name in winners
    if winner:
        marks.append("WINNER")

    action = last_actions.get(player.name, "")
    suffix = f" | {action}" if action else ""
    info = (
        f"{player.position + 1:>2}. {player.name:<10} "
        f"{' '.join(marks):<14} stack ${player.stack:<4} "
        f"bet ${player.current_bet:<4}{suffix}"
    )[:INFO_WIDTH]
    rows = card_rows(player.hand.cards if show_cards else [], hidden_count=2)
    start = "[bold yellow]" if winner else ""
    end = "[/]" if winner else ""
    pad = " " * INFO_WIDTH
    return "\n".join(
        (
            f"{start}{info:<{INFO_WIDTH}}{end} {rows[0]}",
            f"{pad}{rows[1]}",
            f"{pad}{rows[2]}",
        )
    )


def card_rows(cards: list[Card], hidden_count: int = 0) -> tuple[str, str, str]:
    labels = [_card_label(card) for card in cards] or [
        ("┌─────┐", "│ ??  │", "└─────┘")
    ] * hidden_count
    rows = ["", "", ""]
    for label in labels:
        rows[0] += f"{label[0]} "
        rows[1] += f"{label[1]} "
        rows[2] += f"{label[2]} "
    return rows[0].rstrip(), rows[1].rstrip(), rows[2].rstrip()


def _card_label(card: Card) -> tuple[str, str, str]:
    style = "red" if card.suit.value in ("h", "d") else "bright_white"
    return (
        f"[{style}]┌─────┐[/]",
        f"[{style}]│{str(card):^5}│[/]",
        f"[{style}]└─────┘[/]",
    )
