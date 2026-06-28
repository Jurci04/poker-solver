import re
from typing import Any

from textual.app import App
from textual.widgets import Static

from poker_tui.domain.card import Card
from poker_tui.domain.player import Player

COL_WIDTH = 50
COL_GAP = 32
_TAG_RE = re.compile(r"\[[^]]*]")


def update_static(app: App[Any], cache: dict[str, str], selector: str, text: str) -> None:
    if cache.get(selector) != text:
        cache[selector] = text
        app.query_one(selector, Static).update(text)


def board(cards: list[Card]) -> str:
    if not cards:
        return "Board: [--]"
    rows = card_rows(cards)
    return "\n".join(f"{'Board' if i == 0 else '':<6} {row}" for i, row in enumerate(rows))


def players_grid(
    players: list[Player],
    current: Player | None,
    winners: set[str],
    last_actions: dict[str, str],
    show_cards: dict[str, bool],
) -> str:
    split = (len(players) + 1) // 2
    left = [
        player_block(player, current, winners, last_actions, show_cards.get(player.name, False))
        for player in players[:split]
    ]
    right = [
        player_block(player, current, winners, last_actions, show_cards.get(player.name, False))
        for player in players[split:]
    ]
    rows: list[str] = []
    for i in range(split):
        left_lines = left[i]
        right_lines = right[i] if i < len(right) else []
        for line, right_line in zip(
            left_lines,
            right_lines or [""] * len(left_lines),
            strict=False,
        ):
            rows.append(f"{_pad(line, COL_WIDTH)}{' ' * COL_GAP}{right_line}")
    return "\n".join(rows)


def player_block(
    player: Player,
    current: Player | None,
    winners: set[str],
    last_actions: dict[str, str],
    show_cards: bool,
) -> list[str]:
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
        f"{' '.join(marks):<12} stack ${player.stack:<4} "
        f"bet ${player.current_bet:<4}{suffix}"
    )[:COL_WIDTH]
    rows = card_rows(player.hand.cards if show_cards else [], hidden_count=2)
    start = "[bold yellow]" if winner else ""
    end = "[/]" if winner else ""
    return [f"{start}{info:<{COL_WIDTH}}{end}", *rows]


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - len(_TAG_RE.sub("", text)))


def card_rows(cards: list[Card], hidden_count: int = 0) -> tuple[str, ...]:
    labels = [_card_label(card) for card in cards] or [
        ("┌───────┐", "│       │", "│  ??   │", "│       │", "└───────┘")
    ] * hidden_count
    rows = [""] * len(labels[0])
    for label in labels:
        for i, row in enumerate(label):
            rows[i] += f"{row} "
    return tuple(row.rstrip() for row in rows)


def _card_label(card: Card) -> tuple[str, ...]:
    style = "red" if card.suit.value in ("h", "d") else "bright_white"
    return (
        f"[{style}]┌───────┐[/]",
        f"[{style}]│       │[/]",
        f"[{style}]│{str(card):^7}│[/]",
        f"[{style}]│       │[/]",
        f"[{style}]└───────┘[/]",
    )
