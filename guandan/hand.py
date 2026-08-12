"""Hand class – a player's set of cards with combination search."""

from __future__ import annotations
from collections import Counter
from typing import Sequence

from .card import Card
from .constants import CardRank, ComboType


class Hand:
    """A hand of cards with methods to search for playable combinations."""

    def __init__(self, cards: Sequence[Card] | None = None) -> None:
        self.cards: list[Card] = list(cards) if cards else []
        self.sort()

    # -- basic ops ------------------------------------------------------------

    def sort(self) -> None:
        """Sort cards descending by rank point, then suit."""
        self.cards.sort(reverse=True)

    def add(self, card: Card) -> None:
        self.cards.append(card)
        self.sort()

    def remove(self, card: Card) -> None:
        self.cards.remove(card)

    def remove_cards(self, cards: Sequence[Card]) -> None:
        for c in cards:
            self.cards.remove(c)

    def clear(self) -> None:
        self.cards.clear()

    @property
    def size(self) -> int:
        return len(self.cards)

    @property
    def is_empty(self) -> bool:
        return len(self.cards) == 0

    # -- rank helpers ---------------------------------------------------------

    def _rank_counts(self) -> Counter[CardRank]:
        return Counter(c.rank for c in self.cards)

    def _unique_points(self) -> list[int]:
        """Sorted unique point values (descending)."""
        pts = sorted({c.point for c in self.cards}, reverse=True)
        return pts

    def _cards_of_point(self, point: int) -> list[Card]:
        return [c for c in self.cards if c.point == point]

    def _cards_of_rank(self, rank: CardRank) -> list[Card]:
        return [c for c in self.cards if c.rank == rank]

    # -- combination search ---------------------------------------------------

    def get_all_combinations(self) -> dict[ComboType, list[list[str]]]:
        """Return all playable combinations keyed by ComboType.

        Each combination is a list of rank *labels* (strings), e.g. ['A', 'A'].
        """
        return {
            ComboType.SINGLE: self._find_singles(),
            ComboType.PAIR: self._find_pairs(),
            ComboType.TRIPLE: self._find_triples(),
            ComboType.STRAIGHT: self._find_straights(),
            ComboType.TRIPLE_PAIR: self._find_triple_pairs(),
            ComboType.TRIPLE_PLUS_PAIR: self._find_triple_plus_pairs(),
            ComboType.CONSECUTIVE_TRIPLES: self._find_consecutive_triples(),
            ComboType.BOMB: self._find_bombs(),
        }

    def _find_singles(self) -> list[list[str]]:
        pts = self._unique_points()
        return [
            [CardRank.from_point(p).label]
            for p in pts
            if CardRank.from_point(p) not in (CardRank.BLACK_JOKER, CardRank.RED_JOKER)
            or True  # jokers are allowed as singles
        ]

    def _find_pairs(self) -> list[list[str]]:
        counts = self._rank_counts()
        result: list[list[str]] = []
        for rank, cnt in counts.items():
            if cnt >= 2:
                result.append([rank.label, rank.label])
        result.sort(key=lambda x: CardRank.from_label(x[0]).point, reverse=True)
        return result

    def _find_triples(self) -> list[list[str]]:
        counts = self._rank_counts()
        result: list[list[str]] = []
        for rank, cnt in counts.items():
            if cnt >= 3:
                result.append([rank.label] * 3)
        result.sort(key=lambda x: CardRank.from_label(x[0]).point, reverse=True)
        return result

    def _find_straights(self) -> list[list[str]]:
        """5 consecutive ranks (excluding jokers)."""
        pts = [p for p in self._unique_points() if 3 <= p <= 15]
        result: list[list[str]] = []
        for i in range(len(pts) - 4):
            window = pts[i : i + 5]
            if all(
                window[j] == window[j + 1] + 1 for j in range(4)
            ):
                result.append(
                    [CardRank.from_point(p).label for p in window]
                )
        return result

    def _find_triple_pairs(self) -> list[list[str]]:
        """3 consecutive pairs."""
        pair_ranks = [
            CardRank.from_label(p[0])
            for p in self._find_pairs()
        ]
        pair_pts = [r.point for r in pair_ranks]
        result: list[list[str]] = []
        for i in range(len(pair_pts) - 2):
            if pair_pts[i] == pair_pts[i + 1] + 1 == pair_pts[i + 2] + 2:
                r0, r1, r2 = (
                    pair_ranks[i].label,
                    pair_ranks[i + 1].label,
                    pair_ranks[i + 2].label,
                )
                result.append([r0, r0, r1, r1, r2, r2])
        return result

    def _find_triple_plus_pairs(self) -> list[list[str]]:
        """Triple + pair of different rank."""
        triples = self._find_triples()
        pairs = self._find_pairs()
        result: list[list[str]] = []
        for t in triples:
            t_rank = t[0]
            for p in pairs:
                if p[0] != t_rank:
                    result.append(t + p)
                    break  # only need one pair per triple
        return result

    def _find_consecutive_triples(self) -> list[list[str]]:
        """2 consecutive triples."""
        triple_ranks = [
            CardRank.from_label(t[0])
            for t in self._find_triples()
        ]
        triple_pts = [r.point for r in triple_ranks]
        result: list[list[str]] = []
        for i in range(len(triple_pts) - 1):
            if triple_pts[i] == triple_pts[i + 1] + 1:
                r0 = triple_ranks[i].label
                r1 = triple_ranks[i + 1].label
                result.append([r0, r0, r0, r1, r1, r1])
        return result

    def _find_bombs(self) -> list[list[str]]:
        """4+ cards of the same rank."""
        counts = self._rank_counts()
        result: list[list[str]] = []
        for rank, cnt in counts.items():
            if cnt >= 4:
                result.append([rank.label] * cnt)
        result.sort(
            key=lambda x: (len(x), CardRank.from_label(x[0]).point),
            reverse=True,
        )
        return result

    # -- helpers for external use ---------------------------------------------

    @staticmethod
    def classify_combo(labels: list[str]) -> ComboType:
        """Classify a list of rank labels into a ComboType."""
        n = len(labels)
        if n == 0:
            return ComboType.INVALID

        sorted_labels = sorted(
            labels, key=lambda x: CardRank.from_label(x).point, reverse=True
        )
        # helper: points for each label
        pts = [CardRank.from_label(x).point for x in sorted_labels]

        if n == 1:
            return ComboType.SINGLE

        if n == 2:
            if sorted_labels[0] == sorted_labels[1]:
                return ComboType.PAIR
            return ComboType.INVALID

        if n == 3:
            if sorted_labels[0] == sorted_labels[1] == sorted_labels[2]:
                return ComboType.TRIPLE
            return ComboType.INVALID

        if n == 4:
            if len(set(sorted_labels)) == 1:
                return ComboType.BOMB
            return ComboType.INVALID

        if n == 5:
            # could be straight or triple+pair
            if len(set(sorted_labels)) == 5 and all(
                pts[i] == pts[i + 1] + 1 for i in range(4)
            ):
                return ComboType.STRAIGHT
            # triple+pair: 3 of one rank + 2 of another
            counter = Counter(sorted_labels)
            vals = sorted(counter.values())
            if vals == [2, 3]:
                return ComboType.TRIPLE_PLUS_PAIR
            return ComboType.INVALID

        if n == 6:
            counter = Counter(sorted_labels)
            vals = sorted(counter.values())
            # triple pair: 2+2+2
            if vals == [2, 2, 2]:
                ranks = sorted(
                    [CardRank.from_label(r).point for r in counter.keys()],
                    reverse=True,
                )
                if all(ranks[i] == ranks[i + 1] + 1 for i in range(2)):
                    return ComboType.TRIPLE_PAIR
            # consecutive triples: 3+3
            if vals == [3, 3]:
                ranks = sorted(
                    [CardRank.from_label(r).point for r in counter.keys()],
                    reverse=True,
                )
                if ranks[0] == ranks[1] + 1:
                    return ComboType.CONSECUTIVE_TRIPLES
            return ComboType.INVALID

        # n >= 7: bomb if all same
        if len(set(sorted_labels)) == 1:
            return ComboType.BOMB

        return ComboType.INVALID

    @staticmethod
    def compare_combos(
        a_labels: list[str], b_labels: list[str]
    ) -> bool:
        """Return True if combo `a` beats combo `b`.

        `a` is the follower, `b` is the leader. Bombs beat everything.
        Same-type combos are compared by their highest card.
        """
        type_a = Hand.classify_combo(a_labels)
        type_b = Hand.classify_combo(b_labels)

        if type_a == ComboType.INVALID or type_b == ComboType.INVALID:
            return False

        # Bomb beats non-bomb
        if type_a == ComboType.BOMB and type_b != ComboType.BOMB:
            return True
        if type_b == ComboType.BOMB and type_a != ComboType.BOMB:
            return False

        # Both bombs: larger size wins; same size → higher rank wins
        if type_a == ComboType.BOMB and type_b == ComboType.BOMB:
            if len(a_labels) != len(b_labels):
                return len(a_labels) > len(b_labels)
            return _max_point(a_labels) > _max_point(b_labels)

        # Different types
        if type_a != type_b:
            return False

        # Same type: compare
        # For TRIPLE_PLUS_PAIR: only compare the triple part
        if type_a == ComboType.TRIPLE_PLUS_PAIR:
            a_triple = _most_common_label(a_labels)
            b_triple = _most_common_label(b_labels)
            return CardRank.from_label(a_triple).point > CardRank.from_label(
                b_triple
            ).point

        return _max_point(a_labels) > _max_point(b_labels)


# -- internal helpers --------------------------------------------------------


def _max_point(labels: list[str]) -> int:
    return max(CardRank.from_label(x).point for x in labels)


def _most_common_label(labels: list[str]) -> str:
    return Counter(labels).most_common(1)[0][0]
