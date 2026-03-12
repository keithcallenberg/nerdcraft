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
    USE = auto()
    HOTBAR_1 = auto()
    HOTBAR_2 = auto()
    HOTBAR_3 = auto()
    HOTBAR_4 = auto()
    HOTBAR_5 = auto()
    HOTBAR_NEXT = auto()
    HOTBAR_PREV = auto()
    INVENTORY = auto()
    CRAFT = auto()
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
        curses.KEY_UP: Action.JUMP,

        ord('s'): Action.STOP,
        ord('S'): Action.STOP,
        curses.KEY_DOWN: Action.STOP,

        # Actions
        ord(' '): Action.USE,

        # Hotbar
        ord('1'): Action.HOTBAR_1,
        ord('2'): Action.HOTBAR_2,
        ord('3'): Action.HOTBAR_3,
        ord('4'): Action.HOTBAR_4,
        ord('5'): Action.HOTBAR_5,
        ord('e'): Action.HOTBAR_NEXT,
        ord('E'): Action.HOTBAR_NEXT,
        ord('r'): Action.HOTBAR_PREV,
        ord('R'): Action.HOTBAR_PREV,

        # Inventory
        ord('i'): Action.INVENTORY,
        ord('I'): Action.INVENTORY,
        ord('\t'): Action.INVENTORY,

        # Crafting
        ord('c'): Action.CRAFT,
        ord('C'): Action.CRAFT,

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
