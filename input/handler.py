"""Input handling with action mapping."""

from __future__ import annotations
import curses
from enum import Enum, auto


class Action(Enum):
    """Player actions triggered by input."""
    NONE = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    STOP = auto()
    JUMP = auto()
    MINE = auto()
    PLACE = auto()
    QUIT = auto()


class InputHandler:
    """Handles keyboard input and maps to actions."""

    # Key mappings
    KEY_BINDINGS = {
        # Movement
        ord('a'): Action.MOVE_LEFT,
        ord('A'): Action.MOVE_LEFT,
        curses.KEY_LEFT: Action.MOVE_LEFT,

        ord('d'): Action.MOVE_RIGHT,
        ord('D'): Action.MOVE_RIGHT,
        curses.KEY_RIGHT: Action.MOVE_RIGHT,

        ord('w'): Action.JUMP,
        ord('W'): Action.JUMP,
        ord(' '): Action.JUMP,
        curses.KEY_UP: Action.JUMP,

        ord('s'): Action.STOP,
        ord('S'): Action.STOP,
        curses.KEY_DOWN: Action.STOP,

        # Actions
        ord('m'): Action.MINE,
        ord('M'): Action.MINE,

        ord('p'): Action.PLACE,
        ord('P'): Action.PLACE,

        # Quit
        ord('q'): Action.QUIT,
        ord('Q'): Action.QUIT,
        27: Action.QUIT,  # Escape
    }

    def __init__(self):
        """Initialize input handler."""
        self.keys_held: set[int] = set()

    def process_key(self, key: int) -> Action:
        """Process a key press and return the corresponding action."""
        if key == -1:
            return Action.NONE

        return self.KEY_BINDINGS.get(key, Action.NONE)

    def is_move_left_held(self, keys: set[int]) -> bool:
        """Check if move left keys are held."""
        return any(k in keys for k in [ord('a'), ord('A'), curses.KEY_LEFT])

    def is_move_right_held(self, keys: set[int]) -> bool:
        """Check if move right keys are held."""
        return any(k in keys for k in [ord('d'), ord('D'), curses.KEY_RIGHT])

    def get_held_actions(self, keys: set[int]) -> set[Action]:
        """Get all actions for currently held keys."""
        actions = set()
        for key in keys:
            action = self.KEY_BINDINGS.get(key, Action.NONE)
            if action != Action.NONE:
                actions.add(action)
        return actions
