import itertools
from collections import Counter
from enum import IntEnum

from poker_tui.domain.card import Card
from poker_tui.domain.card_utils import cards_to_ints


class HandRank(IntEnum):
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9


_PRIMES = [0, 0, 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]


def _prime_product(card_ints: list[int]) -> int:
    p = 1
    for c in card_ints:
        p *= _PRIMES[(c >> 2) + 2]
    return p


def _check_straight(ranks: list[int]) -> tuple[bool, int]:
    unique = sorted(set(ranks), reverse=True)
    if len(unique) >= 5:
        for i in range(len(unique) - 4):
            if unique[i] - unique[i + 4] == 4:
                return True, unique[i]
    if 14 in ranks and all(r in ranks for r in (2, 3, 4, 5)):
        return True, 5
    return False, 0


def _score_five(card_ints: list[int]) -> int:
    """Score exactly 5 cards. Returns a single sortable int: higher = better hand.
    Packing: bits 31-28 = HandRank, rest = kickers (4 bits each, descending sig)."""
    ranks = sorted([(c >> 2) + 2 for c in card_ints], reverse=True)
    suits = [c & 3 for c in card_ints]
    is_flush = len(set(suits)) == 1
    counts = Counter(ranks)
    groups = sorted(counts.values(), reverse=True)
    is_straight, high = _check_straight(ranks)

    if is_flush and is_straight:
        rv = HandRank.ROYAL_FLUSH if high == 14 else HandRank.STRAIGHT_FLUSH
        return rv << 28 | high << 24

    if groups == [4, 1]:
        quads = next(r for r, c in counts.items() if c == 4)
        kicker = next(r for r, c in counts.items() if c == 1)
        return HandRank.FOUR_OF_A_KIND << 28 | quads << 24 | kicker << 20

    if groups == [3, 2]:
        triple = next(r for r, c in counts.items() if c == 3)
        pair = next(r for r, c in counts.items() if c == 2)
        return HandRank.FULL_HOUSE << 28 | triple << 24 | pair << 20

    if is_flush:
        val = HandRank.FLUSH << 28
        for i, r in enumerate(ranks):
            val |= r << (24 - i * 4)
        return val

    if is_straight:
        return HandRank.STRAIGHT << 28 | high << 24

    if groups == [3, 1, 1]:
        triple = next(r for r, c in counts.items() if c == 3)
        kickers = sorted((r for r, c in counts.items() if c == 1), reverse=True)
        val = HandRank.THREE_OF_A_KIND << 28 | triple << 24
        for i, k in enumerate(kickers):
            val |= k << (20 - i * 4)
        return val

    if groups == [2, 2, 1]:
        pairs = sorted((r for r, c in counts.items() if c == 2), reverse=True)
        kicker = next(r for r, c in counts.items() if c == 1)
        return HandRank.TWO_PAIR << 28 | pairs[0] << 24 | pairs[1] << 20 | kicker << 16

    if groups == [2, 1, 1, 1]:
        pair = next(r for r, c in counts.items() if c == 2)
        kickers = sorted((r for r, c in counts.items() if c == 1), reverse=True)
        val = HandRank.PAIR << 28 | pair << 24
        for i, k in enumerate(kickers):
            val |= k << (20 - i * 4)
        return val

    val = HandRank.HIGH_CARD << 28
    for i, r in enumerate(ranks):
        val |= r << (24 - i * 4)
    return val


def _build_lookup() -> dict[int, int]:
    """Precompute all 5-card evaluations keyed by (prime_product << 1 | flush_bit).

    Generates rank multisets (C(17,5) = 6188) instead of all card combos
    (C(52,5) = 2.6M) — score only depends on rank multiset + flush flag.
    """
    lookup: dict[int, int] = {}
    for ranks in itertools.combinations_with_replacement(range(2, 15), 5):
        suits = [i % 4 for i in range(5)]
        card_ints = [((r - 2) << 2) | suits[i] for i, r in enumerate(ranks)]
        pp = _prime_product(card_ints)
        key = pp << 1 | 0
        if key not in lookup:
            lookup[key] = _score_five(card_ints)
        if len(set(ranks)) == 5:
            flush_ints = [((r - 2) << 2) | 0 for r in ranks]
            key = pp << 1 | 1
            if key not in lookup:
                lookup[key] = _score_five(flush_ints)
    return lookup


_LOOKUP: dict[int, int] = _build_lookup()


class HandEvaluator:
    """Poker hand evaluator using a precomputed lookup table.

    * evaluate(cards) -> (HandRank, kickers_tuple)
    * compare_hands(h1, h2) -> int
    * find_winners(players_and_hands) -> list[str]
    """

    @staticmethod
    def evaluate(cards: list[Card]) -> tuple[HandRank, tuple[int, ...]]:
        if len(cards) < 5:
            ranks = sorted((c.rank.value for c in cards), reverse=True)
            return HandRank.HIGH_CARD, tuple(ranks)

        card_ints = cards_to_ints(cards)
        best_score = -1
        for combo in itertools.combinations(card_ints, 5):
            score = _lookup_score(list(combo))
            if score > best_score:
                best_score = score
        return _decode_score(best_score)

    @staticmethod
    def evaluate_ints(card_ints: list[int]) -> tuple[HandRank, tuple[int, ...]]:
        if len(card_ints) < 5:
            ranks = sorted([(c >> 2) + 2 for c in card_ints], reverse=True)
            return HandRank.HIGH_CARD, tuple(ranks)

        best_score = -1
        for combo in itertools.combinations(card_ints, 5):
            score = _lookup_score(list(combo))
            if score > best_score:
                best_score = score
        return _decode_score(best_score)

    @staticmethod
    def compare_hands(hand1: list[Card], hand2: list[Card]) -> int:
        s1 = HandEvaluator.evaluate(hand1)
        s2 = HandEvaluator.evaluate(hand2)
        return 1 if s1 > s2 else -1 if s1 < s2 else 0

    @staticmethod
    def find_winners(players_and_hands: list[tuple[str, list[Card]]]) -> list[str]:
        if not players_and_hands:
            return []
        best_score = -1
        winners: list[str] = []
        for name, cards in players_and_hands:
            card_ints = cards_to_ints(cards)
            best_combo = -1
            for combo in itertools.combinations(card_ints, 5):
                score = _lookup_score(list(combo))
                if score > best_combo:
                    best_combo = score
            if best_combo > best_score:
                best_score = best_combo
                winners = [name]
            elif best_combo == best_score:
                winners.append(name)
        return winners


def _lookup_score(card_ints: list[int]) -> int:
    pp = _prime_product(card_ints)
    suits = [c & 3 for c in card_ints]
    is_flush = 1 if len(set(suits)) == 1 else 0
    return _LOOKUP.get(pp << 1 | is_flush, 0)


def _decode_score(score: int) -> tuple[HandRank, tuple[int, ...]]:
    handrank = HandRank(score >> 28)
    if handrank in (HandRank.STRAIGHT_FLUSH, HandRank.ROYAL_FLUSH):
        high = (score >> 24) & 0xF
        return handrank, (high,)
    if handrank == HandRank.FOUR_OF_A_KIND:
        quads = (score >> 24) & 0xF
        kicker = (score >> 20) & 0xF
        return handrank, (quads, kicker)
    if handrank == HandRank.FULL_HOUSE:
        triple = (score >> 24) & 0xF
        pair = (score >> 20) & 0xF
        return handrank, (triple, pair)
    if handrank == HandRank.FLUSH:
        kickers = tuple((score >> (24 - i * 4)) & 0xF for i in range(5))
        return handrank, kickers
    if handrank == HandRank.STRAIGHT:
        high = (score >> 24) & 0xF
        return handrank, (high,)
    if handrank == HandRank.THREE_OF_A_KIND:
        triple = (score >> 24) & 0xF
        kickers = tuple((score >> (20 - i * 4)) & 0xF for i in range(2))
        return handrank, (triple, *kickers)
    if handrank == HandRank.TWO_PAIR:
        p1 = (score >> 24) & 0xF
        p2 = (score >> 20) & 0xF
        kicker = (score >> 16) & 0xF
        return handrank, (p1, p2, kicker)
    if handrank == HandRank.PAIR:
        pair = (score >> 24) & 0xF
        kickers = tuple((score >> (20 - i * 4)) & 0xF for i in range(3))
        return handrank, (pair, *kickers)
    # HIGH_CARD
    kickers = tuple((score >> (24 - i * 4)) & 0xF for i in range(5))
    return handrank, kickers
