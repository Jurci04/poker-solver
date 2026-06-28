from poker_tui.domain.card import Card
from poker_tui.domain.enums import Rank, Suit

# 6-bit card encoding: top 4 = rank_index (0-12), bottom 2 = suit_index (0-3).
# rank_index = rank_value - 2  (2->0, 3->1, ..., 14->12)
# suit_index: h=0, d=1, c=2, s=3

_SUIT_TO_IDX: dict[str, int] = {"h": 0, "d": 1, "c": 2, "s": 3}
_IDX_TO_SUIT: dict[int, Suit] = {0: Suit.HEARTS, 1: Suit.DIAMONDS, 2: Suit.CLUBS, 3: Suit.SPADES}


def card_to_int(card: Card) -> int:
    return (card.rank.value - 2) << 2 | _SUIT_TO_IDX[card.suit.value]


def card_from_int(val: int) -> Card:
    rank_val = (val >> 2) + 2
    return Card(rank=Rank(rank_val), suit=_IDX_TO_SUIT[val & 3])


def cards_to_ints(cards: list[Card]) -> list[int]:
    return [card_to_int(c) for c in cards]


def cards_from_ints(vals: list[int]) -> list[Card]:
    return [card_from_int(v) for v in vals]
