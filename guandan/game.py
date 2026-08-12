"""Game state machine and controller for Guandan."""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Callable

import pygame

from .card import Card
from .hand import Hand
from .player import Player
from .ai import AIStrategy, ai_find_cards_for_labels
from .renderer import Renderer
from .constants import (
    CardRank,
    CardSuit,
    ComboType,
    GamePhase,
    Difficulty,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    FPS,
    CARD_WIDTH,
    CARD_GAP,
    PLAYER_HAND_Y_RATIO,
    AI_HAND_Y_RATIO,
    AVATAR_SIZE,
)


@dataclass
class GameConfig:
    """Configuration for a game session."""

    difficulty: Difficulty = Difficulty.NORMAL
    window_width: int = WINDOW_WIDTH
    window_height: int = WINDOW_HEIGHT
    fps: int = FPS


class GameController:
    """Orchestrates the game lifecycle, state machine, and event handling."""

    def __init__(self, config: GameConfig | None = None) -> None:
        self.config = config or GameConfig()

        # Pygame setup
        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.config.window_width, self.config.window_height)
        )
        pygame.display.set_caption("掼蛋 — AI Guandan")
        self.renderer = Renderer(self.screen)
        self._clock = pygame.time.Clock()

        # Game state
        self.phase: GamePhase = GamePhase.PLAYER_INITIATIVE
        self.player = Player(name="你", is_human=True)
        self.ai_player = Player(name="AI", is_human=False)
        self.last_played: list[Card] = []
        self.last_combo_type: ComboType = ComboType.INVALID

        self.ai = AIStrategy(difficulty=self.config.difficulty)
        self.all_cards: list[Card] = []

        # Score & messaging
        self.player_score: int = 0
        self.ai_score: int = 0
        self.message: str = ""
        self._message_timer: int = 0

        # Hint
        self.hint_indices: list[int] = []

        self._running: bool = False

    # -- lifecycle -----------------------------------------------------------

    def run(self) -> None:
        """Main entry point: start and run the game loop."""
        self._setup_game()
        self._running = True
        while self._running:
            self._handle_events()
            self._update()
            self._render()
            self._clock.tick(self.config.fps)
        pygame.quit()

    def _setup_game(self) -> None:
        """Initialize or reset the game for a new round."""
        self._create_deck()
        self._deal_cards()
        self._compute_card_positions()
        self._determine_first_player()
        self.last_played.clear()
        self.last_combo_type = ComboType.INVALID
        self.player.clear_selection()
        self.ai_player.clear_selection()
        self.hint_indices.clear()
        self.message = ""
        self._message_timer = 0

    def _create_deck(self) -> None:
        """Create and shuffle the 54-card deck."""
        cards: list[Card] = []
        for suit in CardSuit:
            for rank in CardRank:
                if rank in (CardRank.BLACK_JOKER, CardRank.RED_JOKER):
                    continue
                cards.append(Card(rank=rank, suit=suit))
        # Add jokers
        cards.append(Card(rank=CardRank.BLACK_JOKER, suit=None))
        cards.append(Card(rank=CardRank.RED_JOKER, suit=None))
        random.shuffle(cards)
        self.all_cards = cards

    def _deal_cards(self) -> None:
        """Deal 27 cards to each player."""
        self.player.hand = Hand(self.all_cards[:27])
        self.ai_player.hand = Hand(self.all_cards[27:])

    def _compute_card_positions(self) -> None:
        """Set up card position layouts."""
        player_y = int(self.config.window_height * PLAYER_HAND_Y_RATIO)
        total_w = 26 * CARD_GAP + CARD_WIDTH
        player_start_x = (self.config.window_width - total_w) // 2

        self.player.compute_card_positions(
            player_start_x, player_y, CARD_WIDTH, CARD_GAP
        )

        ai_y = int(self.config.window_height * AI_HAND_Y_RATIO)
        ai_total_w = 26 * (CARD_GAP // 2) + CARD_WIDTH
        ai_start_x = (self.config.window_width - ai_total_w) // 2
        self.ai_player.compute_card_positions(
            ai_start_x, ai_y, CARD_WIDTH, CARD_GAP // 2
        )

    def _determine_first_player(self) -> None:
        """Player holding 大王 goes first."""
        for card in self.player.hand.cards:
            if card.rank == CardRank.RED_JOKER:
                self.phase = GamePhase.PLAYER_INITIATIVE
                return
        self.phase = GamePhase.AI_INITIATIVE

    # -- event handling ------------------------------------------------------

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
                return

            if event.type == pygame.KEYDOWN:
                self._handle_key(event.key)
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_r and self.phase == GamePhase.GAME_OVER:
            self._restart_game()
        elif key == pygame.K_q:
            self._running = False
        elif key == pygame.K_ESCAPE:
            self._running = False

    def _handle_click(self, pos: tuple[int, int]) -> None:
        if self.phase == GamePhase.GAME_OVER:
            return

        mx, my = pos

        # Card selection (only when it's player's turn)
        if self.phase in (GamePhase.PLAYER_INITIATIVE, GamePhase.PLAYER_FOLLOWING):
            card_idx = self.renderer.get_card_index_at_pos(self.player, mx, my)
            if card_idx is not None:
                self.player.toggle_card(card_idx)
                self.hint_indices.clear()
                return

        # Button clicks
        btn = self.renderer.get_button_clicked(self.phase, mx, my)
        if btn is None:
            return

        if btn == "reset":
            self.player.clear_selection()
            self.hint_indices.clear()

        elif btn == "play":
            self._player_play()

        elif btn == "pass":
            self._player_pass()

        elif btn == "hint":
            self._show_hint()

    # -- player actions ------------------------------------------------------

    def _player_play(self) -> None:
        """Handle player clicking the Play button."""
        labels = self.player.get_selected_labels()
        if not labels:
            self._show_message("请先选择要出的牌")
            return

        combo_type = Hand.classify_combo(labels)
        if combo_type == ComboType.INVALID:
            self._show_message("无效牌型，请重新选择")
            return

        if self.phase == GamePhase.PLAYER_INITIATIVE:
            # Any valid combo is acceptable
            self._execute_player_play()
        elif self.phase == GamePhase.PLAYER_FOLLOWING:
            # Must beat the last played (bombs are handled in compare_combos)
            if not Hand.compare_combos(labels, self._last_played_labels()):
                self._show_message("打不过，请选择更大的牌或不出")
                return
            self._execute_player_play()

    def _execute_player_play(self) -> None:
        """Actually play the selected cards."""
        cards = self.player.play_selected()
        labels = [c.rank.label for c in cards]
        self.last_played = cards
        self.last_combo_type = Hand.classify_combo(labels)

        # Check win
        if self.player.hand.is_empty:
            self._declare_winner(self.player)
            return

        # AI must follow
        self.phase = GamePhase.AI_FOLLOWING
        self.hint_indices.clear()

    def _player_pass(self) -> None:
        """Player chooses not to follow."""
        if self.phase == GamePhase.PLAYER_INITIATIVE:
            self._show_message("你是上家，必须出牌")
            return

        if self.phase == GamePhase.PLAYER_FOLLOWING:
            self.player.clear_selection()
            self.hint_indices.clear()
            # Clear last played - AI gets initiative
            self.last_played.clear()
            self.last_combo_type = ComboType.INVALID
            self.phase = GamePhase.AI_INITIATIVE

    # -- AI actions ----------------------------------------------------------

    def _ai_take_turn(self) -> None:
        """Let the AI make a decision."""
        pygame.time.delay(400)  # Brief pause for UX

        if self.phase == GamePhase.AI_INITIATIVE:
            labels = self.ai.choose_initiative_play(self.ai_player.hand)
            if not labels:
                # Should not happen with a valid hand, but play smallest single
                labels = [self.ai_player.hand.cards[-1].rank.label]
            cards = ai_find_cards_for_labels(self.ai_player.hand.cards, labels)
            self.ai_player.play_cards(cards)
            self.last_played = cards
            self.last_combo_type = Hand.classify_combo(labels)

            if self.ai_player.hand.is_empty:
                self._declare_winner(self.ai_player)
                return

            self.phase = GamePhase.PLAYER_FOLLOWING

        elif self.phase == GamePhase.AI_FOLLOWING:
            leader_labels = self._last_played_labels()
            labels = self.ai.choose_follow_play(
                self.ai_player.hand, leader_labels
            )
            if labels:
                cards = ai_find_cards_for_labels(
                    self.ai_player.hand.cards, labels
                )
                self.ai_player.play_cards(cards)
                self.last_played = cards
                self.last_combo_type = Hand.classify_combo(labels)

                if self.ai_player.hand.is_empty:
                    self._declare_winner(self.ai_player)
                    return

                self.phase = GamePhase.PLAYER_FOLLOWING
            else:
                # AI passes
                self._show_message("AI 不出")
                self.last_played.clear()
                self.last_combo_type = ComboType.INVALID
                self.phase = GamePhase.PLAYER_INITIATIVE

    # -- hint ----------------------------------------------------------------

    def _show_hint(self) -> None:
        """Show a suggested play."""
        self.player.clear_selection()

        if self.phase == GamePhase.PLAYER_INITIATIVE:
            labels = self.ai.choose_initiative_play(self.player.hand)
        elif self.phase == GamePhase.PLAYER_FOLLOWING:
            labels = self.ai.choose_follow_play(
                self.player.hand, self._last_played_labels()
            )
        else:
            return

        if not labels:
            self._show_message("无牌可出，建议不出")
            return

        # Map labels back to card indices
        remaining = list(labels)
        for i, card in enumerate(self.player.hand.cards):
            if card.rank.label in remaining:
                self.player.selected_indices.add(i)
                remaining.remove(card.rank.label)
                self.hint_indices.append(i)
            if not remaining:
                break

    # -- update & render -----------------------------------------------------

    def _update(self) -> None:
        """Update game state."""
        # Decrement message timer
        if self._message_timer > 0:
            self._message_timer -= 1
            if self._message_timer == 0:
                self.message = ""

        # AI auto-play
        if self.phase in (GamePhase.AI_INITIATIVE, GamePhase.AI_FOLLOWING):
            self._ai_take_turn()

    def _render(self) -> None:
        """Draw the current frame."""
        self.renderer.draw_frame(
            phase=self.phase,
            player=self.player,
            ai=self.ai_player,
            last_played=self.last_played,
            message=self.message,
            score=(self.player_score, self.ai_score),
            difficulty=self.config.difficulty,
            hint_cards=self.hint_indices if self.hint_indices else None,
        )
        if self.phase == GamePhase.GAME_OVER:
            winner_name = "你" if self.player.hand.is_empty else "AI"
            self.renderer.draw_game_over(
                winner_name, (self.player_score, self.ai_score)
            )
        pygame.display.flip()

    # -- helpers -------------------------------------------------------------

    def _last_played_labels(self) -> list[str]:
        return [c.rank.label for c in self.last_played]

    def _show_message(self, text: str) -> None:
        self.message = text
        self._message_timer = 90  # ~1.5 seconds at 60fps

    def _declare_winner(self, winner: Player) -> None:
        if winner is self.player:
            self.player_score += 1
        else:
            self.ai_score += 1
        self.phase = GamePhase.GAME_OVER

    def _restart_game(self) -> None:
        """Reset for a new round."""
        self._setup_game()
