"""AI opponent strategies for Guandan."""

from __future__ import annotations
import random
from typing import Sequence

from .card import Card
from .hand import Hand
from .constants import CardRank, ComboType, Difficulty


class AIStrategy:
    """Base class for AI decision-making."""

    def __init__(self, difficulty: Difficulty = Difficulty.NORMAL) -> None:
        self.difficulty = difficulty
        self._rng = random.Random()

    def choose_initiative_play(self, hand: Hand) -> list[str]:
        """Choose what to play when leading a round.

        Returns a list of rank labels, or empty list if no play possible (should not happen).
        """
        combos = hand.get_all_combinations()
        return self._priority_chain(combos)

    def choose_follow_play(
        self, hand: Hand, leader_labels: list[str]
    ) -> list[str]:
        """Choose cards to follow the leader's play.

        Returns a list of rank labels, or empty list to pass.
        """
        combo_type = Hand.classify_combo(leader_labels)
        combos = hand.get_all_combinations()

        # Get playable combos of the same type that beat the leader
        candidates: list[list[str]] = []
        same_type = combos.get(combo_type, [])
        for c in same_type:
            if Hand.compare_combos(c, leader_labels):
                candidates.append(c)

        # Bombs can always beat non-bombs
        if combo_type != ComboType.BOMB:
            for b in combos.get(ComboType.BOMB, []):
                candidates.append(b)

        if not candidates:
            return []

        # Decision logic varies by difficulty
        return self._select_follow_candidate(candidates, combo_type)

    # -- internal -------------------------------------------------------------

    def _priority_chain(
        self, combos: dict[ComboType, list[list[str]]]
    ) -> list[str]:
        """Choose a combo using priority chain, avoiding breaking bombs.

        Priority: straight > triple-pair > triple+pair > triple > consecutive-triples
                  > single/pair (50/50) > bomb
        """
        bombs = combos.get(ComboType.BOMB, [])

        def _break_bomb(candidate: list[str]) -> bool:
            """Check if playing this combo would break a bomb."""
            for b in bombs:
                if candidate[0] in b:
                    return True
            return False

        # Try each priority
        for combo_type in [
            ComboType.STRAIGHT,
            ComboType.TRIPLE_PAIR,
            ComboType.TRIPLE_PLUS_PAIR,
            ComboType.TRIPLE,
            ComboType.CONSECUTIVE_TRIPLES,
        ]:
            options = combos.get(combo_type, [])
            # filter out options that would break bombs (unless hard difficulty)
            if self.difficulty != Difficulty.HARD:
                safe = [o for o in options if not _break_bomb(o)]
            else:
                safe = options
            if safe:
                return safe[0]  # play the strongest of this type
            if options:
                return options[0]

        # Single or pair (50/50)
        singles = combos.get(ComboType.SINGLE, [])
        pairs = combos.get(ComboType.PAIR, [])
        if singles and pairs:
            safe_singles = [s for s in singles if not _break_bomb(s)] if self.difficulty != Difficulty.HARD else singles
            safe_pairs = [p for p in pairs if not _break_bomb(p)] if self.difficulty != Difficulty.HARD else pairs
            if self._rng.random() < 0.5 and safe_singles:
                return safe_singles[0]
            if safe_pairs:
                return safe_pairs[0]
            if safe_singles:
                return safe_singles[0]
        if singles:
            safe = [s for s in singles if not _break_bomb(s)] if self.difficulty != Difficulty.HARD else singles
            if safe:
                return safe[0]
            return singles[0]
        if pairs:
            safe = [p for p in pairs if not _break_bomb(p)] if self.difficulty != Difficulty.HARD else pairs
            if safe:
                return safe[0]
            return pairs[0]

        # Last resort: bomb
        if bombs:
            return bombs[-1]  # play the smallest bomb

        # Should never reach here (hand always has at least 1 card)
        if singles:
            return singles[0]
        return []

    def _select_follow_candidate(
        self, candidates: list[list[str]], leader_type: ComboType
    ) -> list[str]:
        """Select which candidate to play when following.

        Strategy depends on difficulty:
        - Easy: always play the smallest winning combo
        - Normal: use probability to sometimes hold bombs
        - Hard: play optimally with some randomness
        """
        if not candidates:
            return []

        # Sort by strength (weakest first)
        def _strength(c: list[str]) -> int:
            return max(CardRank.from_label(x).point for x in c)

        candidates.sort(key=_strength)

        if self.difficulty == Difficulty.EASY:
            return candidates[0]  # always play weakest

        # Normal/Hard: if using a bomb, sometimes hold it
        my_type = Hand.classify_combo(candidates[0])
        if my_type == ComboType.BOMB and leader_type != ComboType.BOMB:
            # Probability to use bomb increases as opponent has fewer cards
            # (We don't know exact count, but use a heuristic)
            hold_chance = 0.3 if self.difficulty == Difficulty.NORMAL else 0.15
            if self._rng.random() < hold_chance:
                return []  # hold the bomb

        # Play the weakest winning combo
        return candidates[0]


def ai_find_cards_for_labels(
    hand_cards: list[Card], labels: list[str]
) -> list[Card]:
    """Find Card objects matching the given rank labels.

    Used to convert AI's label-based decision back to Card objects.
    """
    result: list[Card] = []
    remaining = list(labels)
    for card in sorted(hand_cards, key=lambda c: c.point):
        if card.rank.label in remaining:
            result.append(card)
            remaining.remove(card.rank.label)
    return result
