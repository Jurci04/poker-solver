import random

from poker_tui.domain.deck import Deck
from poker_tui.domain.enums import Rank, Suit


class TestDeck:
    def test_deck_contains_52_unique_cards(self) -> None:
        d = Deck()
        assert len(d.cards) == 52
        assert len(set(d.cards)) == 52

    def test_shuffle_is_deterministic_with_seed(self) -> None:
        d1 = Deck(rng=random.Random(42))
        d2 = Deck(rng=random.Random(42))
        d1.shuffle()
        d2.shuffle()
        assert d1.cards == d2.cards

    def test_shuffle_differs_with_different_seeds(self) -> None:
        d1 = Deck(rng=random.Random(42))
        d2 = Deck(rng=random.Random(99))
        d1.shuffle()
        d2.shuffle()
        assert d1.cards != d2.cards

    def test_deal_reduces_count(self) -> None:
        d = Deck()
        d.shuffle()
        initial = len(d)
        d.deal(5)
        assert len(d) == initial - 5

    def test_deal_returns_correct_number(self) -> None:
        d = Deck()
        d.shuffle()
        cards = d.deal(3)
        assert len(cards) == 3

    def test_burn_reduces_count(self) -> None:
        d = Deck()
        d.shuffle()
        initial = len(d)
        d.burn()
        assert len(d) == initial - 1

    def test_reset_restores_52(self) -> None:
        d = Deck()
        d.shuffle()
        d.deal(10)
        d.reset()
        assert len(d) == 52

    def test_deal_error_when_not_enough(self) -> None:
        d = Deck()
        d.shuffle()
        import pytest
        with pytest.raises(ValueError):
            d.deal(100)

    def test_all_suits_present(self) -> None:
        d = Deck()
        suits = {c.suit for c in d.cards}
        assert suits == {Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS, Suit.SPADES}

    def test_all_ranks_present(self) -> None:
        d = Deck()
        ranks = {c.rank for c in d.cards}
        assert ranks == set(Rank)
