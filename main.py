#!/usr/bin/env python3
"""Nerdcraft - A 2D side-scroller ASCII game."""

from __future__ import annotations
from typing import Optional
import curses
import sys
import argparse

# Add project root to path for imports
sys.path.insert(0, "/home/keith/projects/nerdcraft")

from game.engine import GameEngine


def main(stdscr, seed: int | None = None) -> None:
    """Main function wrapped by curses."""
    engine = GameEngine(stdscr, seed)
    engine.run()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Nerdcraft - A 2D side-scroller ASCII game"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="World generation seed (random if not specified)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    curses.wrapper(lambda stdscr: main(stdscr, args.seed))
