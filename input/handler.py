"""Input handling with action mapping."""

from __future__ import annotations
import curses
from enum import Enum, auto

from config import GameConfig


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
    CRAFT_CONFIRM = auto()
    QUIT = auto()


class InputHandler:
    """Handles keyboard input and maps to actions."""

    _ACTION_BY_NAME = {
        'move_left': Action.MOVE_LEFT,
        'move_right': Action.MOVE_RIGHT,
        'stop': Action.STOP,
        'jump': Action.JUMP,
        'use': Action.USE,
        'hotbar_1': Action.HOTBAR_1,
        'hotbar_2': Action.HOTBAR_2,
        'hotbar_3': Action.HOTBAR_3,
        'hotbar_4': Action.HOTBAR_4,
        'hotbar_5': Action.HOTBAR_5,
        'hotbar_next': Action.HOTBAR_NEXT,
        'hotbar_prev': Action.HOTBAR_PREV,
        'inventory': Action.INVENTORY,
        'craft': Action.CRAFT,
        'craft_confirm': Action.CRAFT_CONFIRM,
        'quit': Action.QUIT,
    }

    _SPECIAL_KEYS = {
        'KEY_LEFT': curses.KEY_LEFT,
        'KEY_RIGHT': curses.KEY_RIGHT,
        'KEY_UP': curses.KEY_UP,
        'KEY_DOWN': curses.KEY_DOWN,
        'KEY_ENTER': curses.KEY_ENTER,
        'ENTER': 10,
        'RETURN': 13,
        'TAB': ord('\t'),
        'SPACE': ord(' '),
        'ESC': 27,
    }

    def __init__(self):
        """Initialize input handler."""
        self.keys_held: set[int] = set()
        self.KEY_BINDINGS: dict[int, Action] = self._build_key_bindings()

    def _parse_key_token(self, token: str) -> int | None:
        t = token.strip()
        if t in self._SPECIAL_KEYS:
            return self._SPECIAL_KEYS[t]
        if len(t) == 1:
            return ord(t)
        return None

    def _build_key_bindings(self) -> dict[int, Action]:
        cfg = GameConfig.get()
        bindings: dict[int, Action] = {}

        for action_name, key_tokens in cfg.input_bindings.items():
            action = self._ACTION_BY_NAME.get(action_name)
            if action is None:
                continue
            for tok in key_tokens:
                keycode = self._parse_key_token(tok)
                if keycode is not None:
                    bindings[keycode] = action

        return bindings

    def process_key(self, key: int) -> Action:
        """Process a key press and return the corresponding action."""
        if key == -1:
            return Action.NONE

        return self.KEY_BINDINGS.get(key, Action.NONE)

    def is_move_left_held(self, keys: set[int]) -> bool:
        """Check if move left keys are held."""
        return any(self.KEY_BINDINGS.get(k) == Action.MOVE_LEFT for k in keys)

    def is_move_right_held(self, keys: set[int]) -> bool:
        """Check if move right keys are held."""
        return any(self.KEY_BINDINGS.get(k) == Action.MOVE_RIGHT for k in keys)

    def get_held_actions(self, keys: set[int]) -> set[Action]:
        """Get all actions for currently held keys."""
        actions = set()
        for key in keys:
            action = self.KEY_BINDINGS.get(key, Action.NONE)
            if action != Action.NONE:
                actions.add(action)
        return actions
