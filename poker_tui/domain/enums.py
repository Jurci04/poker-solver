from enum import Enum, auto


class Suit(Enum):
    """Card suit with single-character values and display symbols."""
    HEARTS = "h"
    DIAMONDS = "d"
    CLUBS = "c"
    SPADES = "s"

    def __str__(self) -> str:
        return {Suit.HEARTS: "♥", Suit.DIAMONDS: "♦", Suit.CLUBS: "♣", Suit.SPADES: "♠"}[self]


_FACE_MAP: dict[int, str] = {11: "J", 12: "Q", 13: "K", 14: "A"}


class Rank(Enum):
    """Card rank from 2 (lowest) to Ace (highest)."""
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    def __str__(self) -> str:
        return str(self.value) if self.value <= 10 else _FACE_MAP[self.value]


class ActionType(Enum):
    """Legal poker actions."""
    FOLD = auto()
    CHECK = auto()
    CALL = auto()
    BET = auto()
    RAISE = auto()
    ALL_IN = auto()


class Street(Enum):
    """Streets in a hand of Texas Hold'em."""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"

    def __str__(self) -> str:
        return self.value


class PlayerStatus(Enum):
    """Lifecycle state of a player at the table."""
    ACTIVE = auto()
    ALL_IN = auto()
    FOLDED = auto()
    OUT = auto()
