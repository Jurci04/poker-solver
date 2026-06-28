import random

from poker_tui.domain.card import Card
from poker_tui.domain.enums import Rank, Suit


class Deck:
    """Standard 52-card deck with optional seeded RNG for determinism."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng if rng is not None else random.Random()
        self._cards: list[Card] = [Card(rank, suit) for suit in Suit for rank in Rank]
        self._discard: list[Card] = []

    def shuffle(self) -> None:
        self._rng.shuffle(self._cards)

    def deal(self, count: int = 1) -> list[Card]:
        if count > len(self._cards):
            raise ValueError(f"Cannot deal {count} cards, only {len(self._cards)} remaining")
        dealt = self._cards[:count]
        self._cards = self._cards[count:]
        return dealt

    def burn(self) -> None:
        if not self._cards:
            raise ValueError("No cards left to burn")
        self._discard.append(self._cards.pop(0))

    def reset(self) -> None:
        self._cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        self._discard = []
        self.shuffle()

    @property
    def cards(self) -> list[Card]:
        return list(self._cards)

    def __len__(self) -> int:
        return len(self._cards)

    def __repr__(self) -> str:
        return f"Deck({len(self._cards)} cards)"
