from poker_tui.domain.card import Card


def card_boxes(cards: list[Card]) -> str:
    """Render cards as bordered boxes using Rich markup.

    Returns a 5-line string, one set of cards per line (card width = 7 chars).
    """
    if not cards:
        return ""

    lines: list[list[str]] = [[] for _ in range(5)]
    for c in cards:
        color = "red" if c.suit.value in ("h", "d") else "white"
        rank = str(c.rank)
        suit = str(c.suit)
        left = f"{rank:<2}"
        right = f"{rank:>2}"
        chunk = [
            f"[{color}]┌─────┐[/]",
            f"[{color}]│{left}   │[/]",
            f"[{color}]│  {suit}  │[/]",
            f"[{color}]│   {right}│[/]",
            f"[{color}]└─────┘[/]",
        ]
        for i, ch in enumerate(chunk):
            if lines[i]:
                lines[i].append(" ")
            lines[i].append(ch)

    return "\n".join("".join(part) for part in lines)
