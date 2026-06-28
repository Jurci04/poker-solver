from poker_tui.domain.card import Card
from poker_tui.domain.card_utils import card_from_int, card_to_int, cards_from_ints, cards_to_ints
from poker_tui.domain.enums import Rank, Suit
from poker_tui.engine.hand_evaluator import HandEvaluator, HandRank


class TestCardEncoding:
    def test_card_to_int_round_trip(self) -> None:
        for rank in Rank:
            for suit in Suit:
                c = Card(rank, suit)
                val = card_to_int(c)
                assert 0 <= val <= 63, f"Value {val} out of range"
                back = card_from_int(val)
                assert back == c, f"Round trip failed for {c} -> {val} -> {back}"

    def test_cards_to_ints_round_trip(self) -> None:
        cards = [Card(rank, suit) for rank in Rank for suit in Suit]
        vals = cards_to_ints(cards)
        assert len(vals) == 52
        assert len(set(vals)) == 52, "All 52 card ints must be unique"
        back = cards_from_ints(vals)
        assert back == cards


class TestHandEvaluator:
    def _c(self, rank: Rank, suit: Suit = Suit.HEARTS) -> Card:
        return Card(rank, suit)

    def test_high_card(self) -> None:
        cards = [
            self._c(Rank.TWO, Suit.HEARTS), self._c(Rank.FIVE, Suit.DIAMONDS),
            self._c(Rank.NINE, Suit.CLUBS), self._c(Rank.JACK, Suit.SPADES),
            self._c(Rank.KING, Suit.HEARTS),
        ]
        rank, _ = HandEvaluator.evaluate(cards)
        assert rank == HandRank.HIGH_CARD

    def test_pair(self) -> None:
        cards = [
            self._c(Rank.TWO, Suit.HEARTS), self._c(Rank.TWO, Suit.DIAMONDS),
            self._c(Rank.NINE, Suit.CLUBS), self._c(Rank.JACK, Suit.SPADES),
            self._c(Rank.KING, Suit.HEARTS),
        ]
        rank, kickers = HandEvaluator.evaluate(cards)
        assert rank == HandRank.PAIR
        assert kickers[0] == 2

    def test_two_pair(self) -> None:
        cards = [
            self._c(Rank.TWO, Suit.HEARTS), self._c(Rank.TWO, Suit.DIAMONDS),
            self._c(Rank.NINE, Suit.CLUBS), self._c(Rank.NINE, Suit.SPADES),
            self._c(Rank.KING, Suit.HEARTS),
        ]
        rank, _ = HandEvaluator.evaluate(cards)
        assert rank == HandRank.TWO_PAIR

    def test_three_of_a_kind(self) -> None:
        cards = [
            self._c(Rank.TWO, Suit.HEARTS), self._c(Rank.TWO, Suit.DIAMONDS),
            self._c(Rank.TWO, Suit.CLUBS), self._c(Rank.JACK, Suit.SPADES),
            self._c(Rank.KING, Suit.HEARTS),
        ]
        rank, _ = HandEvaluator.evaluate(cards)
        assert rank == HandRank.THREE_OF_A_KIND

    def test_straight(self) -> None:
        cards = [
            self._c(Rank.NINE, Suit.HEARTS), self._c(Rank.TEN, Suit.DIAMONDS),
            self._c(Rank.JACK, Suit.CLUBS), self._c(Rank.QUEEN, Suit.SPADES),
            self._c(Rank.KING, Suit.HEARTS),
        ]
        rank, _ = HandEvaluator.evaluate(cards)
        assert rank == HandRank.STRAIGHT

    def test_straight_with_ace_low(self) -> None:
        cards = [
            self._c(Rank.ACE, Suit.HEARTS), self._c(Rank.TWO, Suit.DIAMONDS),
            self._c(Rank.THREE, Suit.CLUBS), self._c(Rank.FOUR, Suit.SPADES),
            self._c(Rank.FIVE, Suit.HEARTS),
        ]
        rank, _ = HandEvaluator.evaluate(cards)
        assert rank == HandRank.STRAIGHT

    def test_flush(self) -> None:
        cards = [
            self._c(Rank.TWO, Suit.HEARTS), self._c(Rank.FIVE, Suit.HEARTS),
            self._c(Rank.NINE, Suit.HEARTS), self._c(Rank.JACK, Suit.HEARTS),
            self._c(Rank.KING, Suit.HEARTS),
        ]
        rank, _ = HandEvaluator.evaluate(cards)
        assert rank == HandRank.FLUSH

    def test_full_house(self) -> None:
        cards = [
            self._c(Rank.TWO, Suit.HEARTS), self._c(Rank.TWO, Suit.DIAMONDS),
            self._c(Rank.TWO, Suit.CLUBS), self._c(Rank.NINE, Suit.SPADES),
            self._c(Rank.NINE, Suit.HEARTS),
        ]
        rank, _ = HandEvaluator.evaluate(cards)
        assert rank == HandRank.FULL_HOUSE

    def test_four_of_a_kind(self) -> None:
        cards = [
            self._c(Rank.TWO, Suit.HEARTS), self._c(Rank.TWO, Suit.DIAMONDS),
            self._c(Rank.TWO, Suit.CLUBS), self._c(Rank.TWO, Suit.SPADES),
            self._c(Rank.KING, Suit.HEARTS),
        ]
        rank, _ = HandEvaluator.evaluate(cards)
        assert rank == HandRank.FOUR_OF_A_KIND

    def test_straight_flush(self) -> None:
        cards = [
            self._c(Rank.NINE, Suit.HEARTS), self._c(Rank.TEN, Suit.HEARTS),
            self._c(Rank.JACK, Suit.HEARTS), self._c(Rank.QUEEN, Suit.HEARTS),
            self._c(Rank.KING, Suit.HEARTS),
        ]
        rank, _ = HandEvaluator.evaluate(cards)
        assert rank == HandRank.STRAIGHT_FLUSH

    def test_royal_flush(self) -> None:
        cards = [
            self._c(Rank.TEN, Suit.HEARTS), self._c(Rank.JACK, Suit.HEARTS),
            self._c(Rank.QUEEN, Suit.HEARTS), self._c(Rank.KING, Suit.HEARTS),
            self._c(Rank.ACE, Suit.HEARTS),
        ]
        rank, _ = HandEvaluator.evaluate(cards)
        assert rank == HandRank.ROYAL_FLUSH

    def test_best_five_of_seven(self) -> None:
        cards = [
            self._c(Rank.TWO, Suit.HEARTS), self._c(Rank.THREE, Suit.DIAMONDS),
            self._c(Rank.FOUR, Suit.CLUBS), self._c(Rank.FIVE, Suit.SPADES),
            self._c(Rank.SIX, Suit.HEARTS), self._c(Rank.TEN, Suit.DIAMONDS),
            self._c(Rank.JACK, Suit.CLUBS),
        ]
        rank, _ = HandEvaluator.evaluate(cards)
        assert rank == HandRank.STRAIGHT

    def test_best_five_selects_royal_flush(self) -> None:
        cards = [
            self._c(Rank.TWO, Suit.HEARTS),
            self._c(Rank.TEN, Suit.SPADES), self._c(Rank.JACK, Suit.SPADES),
            self._c(Rank.QUEEN, Suit.SPADES), self._c(Rank.KING, Suit.SPADES),
            self._c(Rank.ACE, Suit.SPADES),
            self._c(Rank.THREE, Suit.HEARTS),
        ]
        rank, _ = HandEvaluator.evaluate(cards)
        assert rank == HandRank.ROYAL_FLUSH

    def test_best_five_selects_flush_over_straight(self) -> None:
        cards = [
            self._c(Rank.TWO, Suit.HEARTS), self._c(Rank.FOUR, Suit.HEARTS),
            self._c(Rank.SIX, Suit.HEARTS), self._c(Rank.EIGHT, Suit.HEARTS),
            self._c(Rank.TEN, Suit.HEARTS),
            self._c(Rank.NINE, Suit.DIAMONDS), self._c(Rank.JACK, Suit.DIAMONDS),
        ]
        rank, _ = HandEvaluator.evaluate(cards)
        assert rank == HandRank.FLUSH

    def test_compare_hands_pair_beats_high(self) -> None:
        pair = [
            self._c(Rank.TWO, Suit.HEARTS), self._c(Rank.TWO, Suit.DIAMONDS),
            self._c(Rank.NINE, Suit.CLUBS), self._c(Rank.JACK, Suit.SPADES),
            self._c(Rank.KING, Suit.HEARTS),
        ]
        high = [
            self._c(Rank.THREE, Suit.HEARTS), self._c(Rank.FIVE, Suit.DIAMONDS),
            self._c(Rank.NINE, Suit.CLUBS), self._c(Rank.JACK, Suit.SPADES),
            self._c(Rank.KING, Suit.HEARTS),
        ]
        assert HandEvaluator.compare_hands(pair, high) == 1
        assert HandEvaluator.compare_hands(high, pair) == -1

    def test_find_winners(self) -> None:
        pair = [
            self._c(Rank.TWO, Suit.HEARTS), self._c(Rank.TWO, Suit.DIAMONDS),
            self._c(Rank.NINE, Suit.CLUBS), self._c(Rank.JACK, Suit.SPADES),
            self._c(Rank.KING, Suit.HEARTS),
        ]
        high = [
            self._c(Rank.THREE, Suit.HEARTS), self._c(Rank.FIVE, Suit.DIAMONDS),
            self._c(Rank.NINE, Suit.CLUBS), self._c(Rank.JACK, Suit.SPADES),
            self._c(Rank.KING, Suit.HEARTS),
        ]
        winners = HandEvaluator.find_winners([("Alice", pair), ("Bob", high)])
        assert winners == ["Alice"]

    def test_split_pot(self) -> None:
        cards = [
            self._c(Rank.TWO, Suit.HEARTS), self._c(Rank.FIVE, Suit.DIAMONDS),
            self._c(Rank.NINE, Suit.CLUBS), self._c(Rank.JACK, Suit.SPADES),
            self._c(Rank.KING, Suit.HEARTS),
        ]
        winners = HandEvaluator.find_winners([("Alice", cards), ("Bob", cards)])
        assert len(winners) == 2

    def test_evaluate_ints_round_trip(self) -> None:
        from poker_tui.domain.card_utils import cards_to_ints
        cards = [
            self._c(Rank.NINE, Suit.HEARTS), self._c(Rank.TEN, Suit.HEARTS),
            self._c(Rank.JACK, Suit.HEARTS), self._c(Rank.QUEEN, Suit.HEARTS),
            self._c(Rank.KING, Suit.HEARTS),
        ]
        ints = cards_to_ints(cards)
        rank1, _ = HandEvaluator.evaluate(cards)
        rank2, _ = HandEvaluator.evaluate_ints(ints)
        assert rank1 == rank2

    def test_fewer_than_five_cards(self) -> None:
        cards = [self._c(Rank.ACE), self._c(Rank.KING)]
        rank, kickers = HandEvaluator.evaluate(cards)
        assert rank == HandRank.HIGH_CARD
        assert kickers == (14, 13)

    def test_paired_kickers_in_seven_cards(self) -> None:
        cards = [
            self._c(Rank.ACE, Suit.HEARTS), self._c(Rank.ACE, Suit.DIAMONDS),
            self._c(Rank.KING, Suit.HEARTS), self._c(Rank.KING, Suit.DIAMONDS),
            self._c(Rank.THREE, Suit.HEARTS), self._c(Rank.FOUR, Suit.CLUBS),
            self._c(Rank.SEVEN, Suit.SPADES),
        ]
        rank, kickers = HandEvaluator.evaluate(cards)
        assert rank == HandRank.TWO_PAIR
        assert kickers[0] == 14
        assert kickers[1] == 13
        assert kickers[2] == 7
