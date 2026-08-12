"""Game constants, enums, and configuration."""

from enum import Enum, IntEnum
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root & asset paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
CARDS_DIR = PROJECT_ROOT / "图片集"  # keep original image directory name

# ---------------------------------------------------------------------------
# Card ranks (in game order: 3 lowest, 大王 highest)
# ---------------------------------------------------------------------------
class CardRank(Enum):
    THREE = ("3", 3)
    FOUR = ("4", 4)
    FIVE = ("5", 5)
    SIX = ("6", 6)
    SEVEN = ("7", 7)
    EIGHT = ("8", 8)
    NINE = ("9", 9)
    TEN = ("10", 10)
    J = ("J", 11)
    Q = ("Q", 12)
    K = ("K", 13)
    A = ("A", 14)
    TWO = ("2", 15)
    BLACK_JOKER = ("小王", 16)
    RED_JOKER = ("大王", 17)

    def __init__(self, label: str, point: int):
        self.label = label
        self.point = point

    @classmethod
    def from_label(cls, label: str) -> "CardRank":
        for r in cls:
            if r.label == label:
                return r
        raise KeyError(f"Unknown rank label: {label}")

    @classmethod
    def from_point(cls, point: int) -> "CardRank":
        for r in cls:
            if r.point == point:
                return r
        raise KeyError(f"Unknown rank point: {point}")

    def __str__(self) -> str:
        return self.label


class CardSuit(Enum):
    HEARTS = ("红桃", "♥")
    DIAMONDS = ("方块", "♦")
    SPADES = ("黑桃", "♠")
    CLUBS = ("梅花", "♣")

    def __init__(self, cn_name: str, symbol: str):
        self.cn_name = cn_name
        self.symbol = symbol

    @classmethod
    def from_cn(cls, name: str) -> "CardSuit":
        for s in cls:
            if s.cn_name == name:
                return s
        raise KeyError(f"Unknown suit name: {name}")

    def __str__(self) -> str:
        return self.cn_name


class ComboType(IntEnum):
    """Card combination types, ordered by rank for comparison."""
    INVALID = 0
    SINGLE = 1
    PAIR = 2
    TRIPLE = 3
    STRAIGHT = 4
    TRIPLE_PAIR = 5
    TRIPLE_PLUS_PAIR = 6
    CONSECUTIVE_TRIPLES = 7
    BOMB = 8


class GamePhase(Enum):
    PLAYER_INITIATIVE = "player_initiative"
    AI_INITIATIVE = "ai_initiative"
    PLAYER_FOLLOWING = "player_following"
    AI_FOLLOWING = "ai_following"
    GAME_OVER = "game_over"


class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


# ---------------------------------------------------------------------------
# Color palette  (modern dark casino theme)
# ---------------------------------------------------------------------------
class Colors:
    # Table
    TABLE_GREEN = (21, 58, 42)
    TABLE_FELT = (27, 74, 53)
    TABLE_BORDER = (45, 106, 79)

    # Panels
    PANEL_BG = (18, 24, 38, 220)  # dark navy with alpha
    PANEL_BORDER = (45, 55, 72)

    # Cards
    CARD_FACE = (255, 254, 249)
    CARD_BACK = (30, 60, 114)
    CARD_BORDER = (180, 160, 120)
    CARD_SELECTED = (255, 215, 0)
    CARD_RED = (200, 40, 40)
    CARD_BLACK = (30, 30, 30)
    CARD_SHADOW = (0, 0, 0, 80)

    # Buttons
    BTN_DEFAULT = (55, 65, 81)
    BTN_HOVER = (75, 85, 99)
    BTN_PRIMARY = (37, 99, 235)
    BTN_PRIMARY_HOVER = (59, 130, 246)
    BTN_DANGER = (185, 28, 28)
    BTN_DANGER_HOVER = (220, 38, 38)
    BTN_SUCCESS = (21, 128, 61)
    BTN_TEXT = (255, 255, 255)

    # Text
    TEXT_PRIMARY = (240, 240, 240)
    TEXT_SECONDARY = (160, 170, 180)
    TEXT_GOLD = (232, 197, 71)
    TEXT_RED = (248, 113, 113)

    # Accents
    GOLD = (232, 197, 71)
    GOLD_DARK = (180, 150, 50)


# ---------------------------------------------------------------------------
# Layout & sizing
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 60

CARD_WIDTH = 85
CARD_HEIGHT = 120
CARD_GAP = 22
CARD_LIFT = 25

BUTTON_WIDTH = 140
BUTTON_HEIGHT = 44
BUTTON_GAP = 10

PLAYED_CARD_GAP = 18
PLAYED_AREA_Y_RATIO = 0.42

# Player hand position (bottom)
PLAYER_HAND_Y_RATIO = 0.78
# AI hand position (top)
AI_HAND_Y_RATIO = 0.04

# Avatar
AVATAR_SIZE = 70
AVATAR_MARGIN = 20

# Font sizes
FONT_SMALL = 16
FONT_NORMAL = 20
FONT_LARGE = 28
FONT_XL = 42
FONT_TITLE = 56

# Card rank display mapping (for programmatic rendering)
RANK_DISPLAY = {
    "3": "3", "4": "4", "5": "5", "6": "6", "7": "7",
    "8": "8", "9": "9", "10": "10", "J": "J", "Q": "Q",
    "K": "K", "A": "A", "2": "2", "小王": "小", "大王": "大",
}
