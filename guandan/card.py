"""Card class representing a single playing card."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

from .constants import CardRank, CardSuit, CARDS_DIR


@dataclass
class Card:
    """A single playing card with rank and suit.

    Jokers are represented with suit=None and rank=BLACK_JOKER/RED_JOKER.
    """

    rank: CardRank
    suit: CardSuit | None = None

    # cached fields
    _image_path: Path | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self._image_path = self._resolve_image_path()

    # -- properties ----------------------------------------------------------

    @property
    def point(self) -> int:
        """Numeric value for comparison (3=3 .. 2=15, 小王=16, 大王=17)."""
        return self.rank.point

    @property
    def is_joker(self) -> bool:
        return self.rank in (CardRank.BLACK_JOKER, CardRank.RED_JOKER)

    @property
    def is_red(self) -> bool:
        """Red-colored suits + red joker for display."""
        if self.rank == CardRank.RED_JOKER:
            return True
        return self.suit in (CardSuit.HEARTS, CardSuit.DIAMONDS)

    @property
    def display_name(self) -> str:
        """Human-readable card name, e.g. '红桃A', '大王'."""
        if self.is_joker:
            return self.rank.label
        assert self.suit is not None
        return f"{self.suit.cn_name}{self.rank.label}"

    @property
    def image_path(self) -> Path:
        """Filesystem path to the card's PNG image."""
        assert self._image_path is not None
        return self._image_path

    @property
    def color_rgb(self) -> tuple[int, int, int]:
        """Display color for the card's text."""
        if self.is_red:
            return (200, 40, 40)
        return (30, 30, 30)

    # -- internal ------------------------------------------------------------

    def _resolve_image_path(self) -> Path:
        if self.is_joker:
            return CARDS_DIR / f"{self.rank.label}.png"
        assert self.suit is not None
        return CARDS_DIR / f"{self.suit.cn_name}{self.rank.label}.png"

    # -- rich comparison (delegates to rank.point, then suit for tie-break) --

    def _compare_key(self) -> tuple[int, int]:
        suit_order = (
            self.suit.value if self.suit else 99
        )  # jokers sort after suits
        return (self.point, suit_order)

    def __lt__(self, other: Card) -> bool:
        return self._compare_key() < other._compare_key()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))

    def __repr__(self) -> str:
        return f"Card({self.display_name})"
