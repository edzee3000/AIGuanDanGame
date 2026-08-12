"""Player class – shared logic for human and AI players."""

from __future__ import annotations
from dataclasses import dataclass, field

from .card import Card
from .hand import Hand
from .constants import CardRank, ComboType


@dataclass
class Player:
    """Represents a player (human or AI) in the game."""

    name: str
    is_human: bool = True
    hand: Hand = field(default_factory=Hand)
    avatar_pos: tuple[int, int] = (0, 0)
    avatar_size: tuple[int, int] = (70, 70)

    # card rendering positions
    card_positions: list[tuple[int, int]] = field(default_factory=list)
    card_raised: list[bool] = field(default_factory=list)

    # currently selected cards (indices into hand.cards)
    selected_indices: set[int] = field(default_factory=set)

    # tracking
    rounds_won: int = 0

    # -- card position management --------------------------------------------

    def compute_card_positions(
        self,
        first_x: int,
        first_y: int,
        card_width: int,
        card_gap: int,
        max_cards: int = 27,
    ) -> None:
        """Pre-compute positions for all possible card slots."""
        self.card_positions = [
            (first_x + i * card_gap, first_y) for i in range(max_cards)
        ]
        self.card_raised = [False] * max_cards

    # -- selection -----------------------------------------------------------

    def toggle_card(self, index: int) -> None:
        """Toggle selection state of a card by index."""
        if index < 0 or index >= self.hand.size:
            return
        if index in self.selected_indices:
            self.selected_indices.discard(index)
        else:
            self.selected_indices.add(index)

    def clear_selection(self) -> None:
        self.selected_indices.clear()

    def get_selected_cards(self) -> list[Card]:
        """Return Card objects for the currently selected indices (in hand order)."""
        indices = sorted(self.selected_indices, reverse=True)
        return [self.hand.cards[i] for i in indices]

    def get_selected_labels(self) -> list[str]:
        """Return rank labels of selected cards."""
        return [c.rank.label for c in self.get_selected_cards()]

    # -- actions -------------------------------------------------------------

    def play_selected(self) -> list[Card]:
        """Remove and return the selected cards from hand."""
        cards = self.get_selected_cards()
        self.hand.remove_cards(cards)
        self.clear_selection()
        return cards

    def play_cards(self, cards: list[Card]) -> None:
        """Remove given cards from hand."""
        self.hand.remove_cards(cards)
        self.clear_selection()
