#!/usr/bin/env python3
"""Nerdcraft - A 2D side-scroller ASCII game."""

from __future__ import annotations
import curses
import sys
import argparse
from pathlib import Path

# Ensure project root is on the path regardless of where we're launched from
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from game.engine import GameEngine


def main(stdscr, args: argparse.Namespace) -> None:
    """Main function wrapped by curses."""
    engine = GameEngine(stdscr, seed=args.seed, save_name=args.save, force_new=args.new)
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
    parser.add_argument(
        "--save", "-n",
        type=str,
        default="default",
        help="Save slot name (default: 'default')"
    )
    parser.add_argument(
        "--new",
        action="store_true",
        default=False,
        help="Force generation of a new world (ignore existing save)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    curses.wrapper(lambda stdscr: main(stdscr, args))
