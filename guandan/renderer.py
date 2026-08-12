"""Pygame rendering for the Guandan card game."""

from __future__ import annotations
import math
from pathlib import Path
from typing import Sequence

import pygame

from .card import Card
from .constants import (
    Colors,
    CardSuit,
    CardRank,
    ComboType,
    GamePhase,
    Difficulty,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    CARD_WIDTH,
    CARD_HEIGHT,
    CARD_GAP,
    CARD_LIFT,
    BUTTON_WIDTH,
    BUTTON_HEIGHT,
    BUTTON_GAP,
    PLAYED_CARD_GAP,
    PLAYED_AREA_Y_RATIO,
    PLAYER_HAND_Y_RATIO,
    AI_HAND_Y_RATIO,
    AVATAR_SIZE,
    AVATAR_MARGIN,
    FONT_SMALL,
    FONT_NORMAL,
    FONT_LARGE,
    FONT_XL,
    FONT_TITLE,
    CARDS_DIR,
)
from .hand import Hand
from .player import Player

# ---------------------------------------------------------------------------
# Font loading
# ---------------------------------------------------------------------------

def _load_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Load a font that supports Chinese characters."""
    # Try common CJK fonts
    candidates = [
        "SimHei", "Microsoft YaHei", "PingFang SC",
        "Noto Sans CJK SC", "WenQuanYi Micro Hei",
        "Arial", "sans-serif",
    ]
    for name in candidates:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            continue
    return pygame.font.Font(None, size)


# Pre-load fonts at module level
_font_small = _load_font(FONT_SMALL)
_font_normal = _load_font(FONT_NORMAL)
_font_large = _load_font(FONT_LARGE)
_font_xl = _load_font(FONT_XL, bold=True)
_font_title = _load_font(FONT_TITLE, bold=True)


# ---------------------------------------------------------------------------
# Card-back cache
# ---------------------------------------------------------------------------

_card_back_surface: pygame.Surface | None = None


def _get_card_back() -> pygame.Surface:
    """Create a cached card-back surface with a nice pattern."""
    global _card_back_surface
    if _card_back_surface is not None:
        return _card_back_surface

    surf = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)

    # Background
    pygame.draw.rect(surf, Colors.CARD_BACK, (0, 0, CARD_WIDTH, CARD_HEIGHT), border_radius=8)

    # Diamond pattern
    for x in range(8, CARD_WIDTH - 4, 16):
        for y in range(8, CARD_HEIGHT - 4, 16):
            pygame.draw.rect(
                surf,
                (45, 80, 140),
                (x, y, 10, 10),
                border_radius=2,
            )

    # Border
    pygame.draw.rect(
        surf, Colors.CARD_BORDER, (0, 0, CARD_WIDTH, CARD_HEIGHT), width=2, border_radius=8
    )

    _card_back_surface = surf
    return surf


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------

class Renderer:
    """Handles all drawing for the game."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self._clock = pygame.time.Clock()
        self._anim_tick = 0

        # Cache loaded card images
        self._image_cache: dict[Path, pygame.Surface] = {}

    # -- public API ----------------------------------------------------------

    def tick(self, fps: int = 60) -> None:
        self._clock.tick(fps)
        self._anim_tick += 1

    def draw_frame(
        self,
        phase: GamePhase,
        player: Player,
        ai: Player,
        last_played: list[Card],
        message: str = "",
        score: tuple[int, int] = (0, 0),
        difficulty: Difficulty = Difficulty.NORMAL,
        hint_cards: list[int] | None = None,
    ) -> None:
        """Draw a complete game frame."""
        self._draw_background()
        self._draw_ai_hand(ai)
        self._draw_player_hand(player, hint_cards)
        self._draw_played_cards(last_played)
        self._draw_buttons(phase)
        self._draw_status_bar(player, ai, phase, message, score, difficulty)

    def draw_game_over(
        self, winner_name: str, score: tuple[int, int]
    ) -> None:
        """Draw game-over overlay."""
        # Dim background
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill((10, 10, 20))
        self.screen.blit(overlay, (0, 0))

        # Title
        title = _font_title.render(
            f"{'🎉 ' if '你' in winner_name else '😔 '}{winner_name} 获胜！",
            True,
            Colors.TEXT_GOLD,
        )
        title_rect = title.get_rect(center=(self.width // 2, self.height // 2 - 80))
        self.screen.blit(title, title_rect)

        # Score
        score_text = _font_large.render(
            f"比分  {score[0]} : {score[1]}",
            True,
            Colors.TEXT_PRIMARY,
        )
        score_rect = score_text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(score_text, score_rect)

        # Restart hint
        hint = _font_normal.render(
            "按 R 键重新开始  |  按 Q 退出",
            True,
            Colors.TEXT_SECONDARY,
        )
        hint_rect = hint.get_rect(center=(self.width // 2, self.height // 2 + 80))
        self.screen.blit(hint, hint_rect)

    # -- background ----------------------------------------------------------

    def _draw_background(self) -> None:
        """Draw the felt table background."""
        # Load and scale table image, or use color fill
        table_path = CARDS_DIR / "牌桌.jpg"
        if table_path.exists():
            try:
                bg = pygame.image.load(str(table_path)).convert()
                bg = pygame.transform.scale(bg, (self.width, self.height))
                self.screen.blit(bg, (0, 0))
                return
            except Exception:
                pass

        # Fallback: gradient green background
        for y in range(self.height):
            ratio = y / self.height
            r = int(Colors.TABLE_GREEN[0] * (1 - ratio) + Colors.TABLE_FELT[0] * ratio)
            g = int(Colors.TABLE_GREEN[1] * (1 - ratio) + Colors.TABLE_FELT[1] * ratio)
            b = int(Colors.TABLE_GREEN[2] * (1 - ratio) + Colors.TABLE_FELT[2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))

    # -- cards ---------------------------------------------------------------

    def _load_card_image(self, card: Card) -> pygame.Surface:
        """Load card image with caching."""
        path = card.image_path
        if path not in self._image_cache:
            try:
                img = pygame.image.load(str(path)).convert()
                img = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
                self._image_cache[path] = img
            except Exception:
                # Fallback: create a simple card surface
                img = self._create_fallback_card(card)
                self._image_cache[path] = img
        return self._image_cache[path]

    def _create_fallback_card(self, card: Card) -> pygame.Surface:
        """Create a simple text-based card when image is unavailable."""
        surf = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)

        # Card background
        pygame.draw.rect(
            surf, Colors.CARD_FACE, (0, 0, CARD_WIDTH, CARD_HEIGHT), border_radius=6
        )
        pygame.draw.rect(
            surf, Colors.CARD_BORDER, (0, 0, CARD_WIDTH, CARD_HEIGHT), width=2, border_radius=6
        )

        if not card.is_joker:
            assert card.suit is not None
            # Rank text
            rank_text = _font_normal.render(card.rank.label, True, card.color_rgb)
            surf.blit(rank_text, (8, 6))

            # Suit symbol
            suit_text = _font_small.render(card.suit.symbol, True, card.color_rgb)
            surf.blit(suit_text, (8, 28))

            # Center large suit
            center_suit = _font_large.render(card.suit.symbol, True, card.color_rgb)
            suit_rect = center_suit.get_rect(
                center=(CARD_WIDTH // 2, CARD_HEIGHT // 2)
            )
            surf.blit(center_suit, suit_rect)
        else:
            label = "大" if card.rank == CardRank.RED_JOKER else "小"
            color = (200, 40, 40) if card.rank == CardRank.RED_JOKER else (30, 30, 30)
            text = _font_large.render(label, True, color)
            text_rect = text.get_rect(center=(CARD_WIDTH // 2, CARD_HEIGHT // 2))
            surf.blit(text, text_rect)

        return surf

    def _draw_card_at(
        self,
        card: Card | None,
        x: int,
        y: int,
        raised: bool = False,
        face_down: bool = False,
        highlight: bool = False,
    ) -> None:
        """Draw a single card at a position."""
        if card is None:
            return

        ry = y - (CARD_LIFT if raised else 0)

        # Shadow
        shadow_surf = pygame.Surface((CARD_WIDTH + 6, CARD_HEIGHT + 6), pygame.SRCALPHA)
        if raised:
            shadow_color = (0, 0, 0, 100)
        else:
            shadow_color = (0, 0, 0, 40)
        pygame.draw.rect(
            shadow_surf,
            shadow_color,
            (0, 0, CARD_WIDTH + 6, CARD_HEIGHT + 6),
            border_radius=8,
        )
        self.screen.blit(shadow_surf, (x - 3, ry - 3))

        if face_down:
            card_surf = _get_card_back()
        else:
            card_surf = self._load_card_image(card)

        # Highlight border for selected/hint cards
        if highlight:
            hl_surf = pygame.Surface((CARD_WIDTH + 4, CARD_HEIGHT + 4), pygame.SRCALPHA)
            pygame.draw.rect(
                hl_surf,
                Colors.CARD_SELECTED,
                (0, 0, CARD_WIDTH + 4, CARD_HEIGHT + 4),
                border_radius=8,
                width=3,
            )
            self.screen.blit(hl_surf, (x - 2, ry - 2))

        self.screen.blit(card_surf, (x, ry))

    # -- hand drawing --------------------------------------------------------

    def _draw_player_hand(
        self, player: Player, hint_indices: list[int] | None = None
    ) -> None:
        """Draw the human player's hand at the bottom."""
        if player.hand.is_empty:
            return

        n = player.hand.size
        # Calculate starting x to center the hand
        total_width = (n - 1) * CARD_GAP + CARD_WIDTH
        start_x = (self.width - total_width) // 2
        card_y = int(self.height * PLAYER_HAND_Y_RATIO)

        for i, card in enumerate(player.hand.cards):
            x = start_x + i * CARD_GAP
            is_raised = i in player.selected_indices
            is_hint = hint_indices is not None and i in hint_indices
            self._draw_card_at(
                card, x, card_y,
                raised=is_raised,
                highlight=is_hint or is_raised,
            )

        # Player name label
        name_text = _font_small.render(
            f"你  ({player.hand.size} 张)", True, Colors.TEXT_PRIMARY
        )
        self.screen.blit(name_text, (start_x, card_y + CARD_HEIGHT + 6))

    def _draw_ai_hand(self, ai: Player) -> None:
        """Draw the AI's hand face-down at the top."""
        if ai.hand.is_empty:
            return

        n = ai.hand.size
        total_width = (n - 1) * (CARD_GAP // 2) + CARD_WIDTH
        start_x = (self.width - total_width) // 2
        card_y = int(self.height * AI_HAND_Y_RATIO)

        for i in range(n):
            x = start_x + i * (CARD_GAP // 2)
            self._draw_card_at(None, x, card_y, face_down=True)

        # AI name label
        name_text = _font_small.render(
            f"AI  ({ai.hand.size} 张)", True, Colors.TEXT_SECONDARY
        )
        self.screen.blit(name_text, (start_x, card_y - 20))

    # -- played cards --------------------------------------------------------

    def _draw_played_cards(self, cards: list[Card]) -> None:
        """Draw the last played cards in the center."""
        if not cards:
            return

        n = len(cards)
        total_width = (n - 1) * PLAYED_CARD_GAP + CARD_WIDTH
        start_x = (self.width - total_width) // 2
        card_y = int(self.height * PLAYED_AREA_Y_RATIO)

        # Area label
        area_text = _font_small.render("上次出牌", True, Colors.TEXT_SECONDARY)
        text_rect = area_text.get_rect(
            centerx=self.width // 2, bottom=card_y - 8
        )
        self.screen.blit(area_text, text_rect)

        for i, card in enumerate(cards):
            x = start_x + i * PLAYED_CARD_GAP
            self._draw_card_at(card, x, card_y)

    # -- buttons -------------------------------------------------------------

    def _draw_buttons(self, phase: GamePhase) -> None:
        """Draw action buttons on the right side."""
        margin = 20
        btn_x = self.width - BUTTON_WIDTH - margin
        btn_y = int(self.height * 0.55)

        buttons = []

        if phase in (GamePhase.PLAYER_INITIATIVE, GamePhase.PLAYER_FOLLOWING):
            buttons.extend([
                ("出  牌", Colors.BTN_PRIMARY, Colors.BTN_PRIMARY_HOVER),
                ("不  出", Colors.BTN_DANGER, Colors.BTN_DANGER_HOVER),
                ("提  示", Colors.BTN_SUCCESS, (60, 180, 80)),
                ("重  置", Colors.BTN_DEFAULT, Colors.BTN_HOVER),
            ])
        else:
            # AI's turn - show disabled buttons
            buttons.extend([
                ("出  牌", (80, 80, 90), (80, 80, 90)),
                ("不  出", (80, 80, 90), (80, 80, 90)),
                ("提  示", (80, 80, 90), (80, 80, 90)),
                ("重  置", (80, 80, 90), (80, 80, 90)),
            ])

        mouse_x, mouse_y = pygame.mouse.get_pos()

        for i, (label, color, hover_color) in enumerate(buttons):
            y = btn_y + i * (BUTTON_HEIGHT + BUTTON_GAP)
            btn_rect = pygame.Rect(btn_x, y, BUTTON_WIDTH, BUTTON_HEIGHT)

            # Check hover
            is_hover = btn_rect.collidepoint(mouse_x, mouse_y)

            # Draw button background
            c = hover_color if is_hover else color
            pygame.draw.rect(
                self.screen, c, btn_rect, border_radius=8
            )
            # Border
            pygame.draw.rect(
                self.screen,
                Colors.PANEL_BORDER,
                btn_rect,
                width=1,
                border_radius=8,
            )

            # Label
            text = _font_normal.render(label, True, Colors.BTN_TEXT)
            text_rect = text.get_rect(center=btn_rect.center)
            self.screen.blit(text, text_rect)

    # -- status bar ----------------------------------------------------------

    def _draw_status_bar(
        self,
        player: Player,
        ai: Player,
        phase: GamePhase,
        message: str,
        score: tuple[int, int],
        difficulty: Difficulty,
    ) -> None:
        """Draw the top status bar with scores, phase info, and messages."""
        # Semi-transparent panel
        panel_rect = pygame.Rect(0, 0, self.width, 44)
        panel = pygame.Surface((self.width, 44))
        panel.set_alpha(200)
        panel.fill((15, 23, 42))
        self.screen.blit(panel, (0, 0))

        # Score
        score_text = _font_normal.render(
            f"你  {score[0]} : {score[1]}  AI", True, Colors.TEXT_GOLD
        )
        self.screen.blit(score_text, (12, 10))

        # Phase
        phase_map = {
            GamePhase.PLAYER_INITIATIVE: "你的回合 — 请出牌",
            GamePhase.AI_INITIATIVE: "AI 思考中...",
            GamePhase.PLAYER_FOLLOWING: "请跟牌或不出",
            GamePhase.AI_FOLLOWING: "AI 思考中...",
            GamePhase.GAME_OVER: "游戏结束",
        }
        phase_text = _font_small.render(
            phase_map.get(phase, ""), True, Colors.TEXT_SECONDARY
        )
        self.screen.blit(
            phase_text, (self.width // 2 - phase_text.get_width() // 2, 12)
        )

        # Difficulty badge
        diff_color = {
            Difficulty.EASY: (100, 200, 100),
            Difficulty.NORMAL: (232, 197, 71),
            Difficulty.HARD: (248, 113, 113),
        }
        diff_text = _font_small.render(
            difficulty.value.upper(), True, diff_color.get(difficulty, Colors.TEXT_SECONDARY)
        )
        self.screen.blit(diff_text, (self.width - diff_text.get_width() - 24, 14))

        # Message overlay
        if message:
            msg_surf = pygame.Surface((self.width, 60))
            msg_surf.set_alpha(160)
            msg_surf.fill((0, 0, 0))
            msg_rect = msg_surf.get_rect(
                center=(self.width // 2, self.height // 2 + 100)
            )
            self.screen.blit(msg_surf, msg_rect)

            msg_text = _font_large.render(message, True, Colors.TEXT_PRIMARY)
            msg_text_rect = msg_text.get_rect(center=msg_rect.center)
            self.screen.blit(msg_text, msg_text_rect)

    # -- helpers -------------------------------------------------------------

    def get_card_index_at_pos(
        self, player: Player, mouse_x: int, mouse_y: int
    ) -> int | None:
        """Determine which card in the player's hand was clicked. Returns index or None."""
        if player.hand.is_empty:
            return None

        n = player.hand.size
        total_width = (n - 1) * CARD_GAP + CARD_WIDTH
        start_x = (self.width - total_width) // 2
        card_y = int(self.height * PLAYER_HAND_Y_RATIO)
        card_bottom = card_y + CARD_HEIGHT

        if not (card_y <= mouse_y <= card_bottom):
            return None

        for i in range(n):
            card_left = start_x + i * CARD_GAP
            card_right = card_left + CARD_WIDTH
            if card_left <= mouse_x <= card_right:
                return i
        return None

    def get_button_clicked(self, phase: GamePhase, mouse_x: int, mouse_y: int) -> str | None:
        """Determine which button was clicked. Returns button name or None."""
        margin = 20
        btn_x = self.width - BUTTON_WIDTH - margin
        btn_y = int(self.height * 0.55)

        button_names = ["play", "pass", "hint", "reset"]

        for i, name in enumerate(button_names):
            y = btn_y + i * (BUTTON_HEIGHT + BUTTON_GAP)
            btn_rect = pygame.Rect(btn_x, y, BUTTON_WIDTH, BUTTON_HEIGHT)
            if btn_rect.collidepoint(mouse_x, mouse_y):
                return name
        return None
