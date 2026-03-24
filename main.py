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
from game.menu import MainMenu


def main(stdscr, args: argparse.Namespace) -> None:
    """Main function wrapped by curses."""
    seed = args.seed
    save_name = args.save
    force_new = args.new
    world_size_chunks = None

    # Show menu by default unless explicit CLI world args are provided.
    explicit_cli_world = (args.seed is not None) or args.new or (args.save != "default")
    if not explicit_cli_world:
        menu_result = MainMenu(stdscr).run()
        if not menu_result.start_game:
            return
        seed = menu_result.seed
        save_name = menu_result.save_name
        force_new = menu_result.force_new
        world_size_chunks = menu_result.world_size_chunks

    engine = GameEngine(
        stdscr,
        seed=seed,
        save_name=save_name,
        force_new=force_new,
        world_size_chunks=world_size_chunks,
    )
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
