"""Entry point for the Guandan card game."""

import argparse
import sys
from pathlib import Path

# Ensure the project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from guandan.game import GameController, GameConfig
from guandan.constants import Difficulty


def main() -> None:
    parser = argparse.ArgumentParser(
        description="掼蛋 — AI Guandan Card Game"
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "normal", "hard"],
        default="normal",
        help="AI difficulty level (default: normal)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1200,
        help="Window width (default: 1200)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=800,
        help="Window height (default: 800)",
    )
    args = parser.parse_args()

    difficulty_map = {
        "easy": Difficulty.EASY,
        "normal": Difficulty.NORMAL,
        "hard": Difficulty.HARD,
    }

    config = GameConfig(
        difficulty=difficulty_map[args.difficulty],
        window_width=args.width,
        window_height=args.height,
    )

    game = GameController(config)
    game.run()


if __name__ == "__main__":
    main()
