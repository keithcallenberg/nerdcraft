"""Player entity with integer grid position."""

from __future__ import annotations

from config import GameConfig
from entity.inventory import Inventory


class Player:
    """The player entity occupying a single cell."""

    def __init__(self, x: int = 0, y: int = 0):
        """Initialize player at given grid position."""
        self.x = x
        self.y = y
        self.on_ground = False
        self.facing_right = True
        self.jump_remaining = 0  # blocks left to rise
        self.health = GameConfig.get().combat.max_health
        self.fall_distance = 0  # blocks fallen continuously
        self.inventory = Inventory()

    def get_block_in_direction(self, direction: str) -> tuple[int, int]:
        """Get the adjacent block position for a direction."""
        if direction == 'left':
            return (self.x - 1, self.y)
        elif direction == 'right':
            return (self.x + 1, self.y)
        elif direction == 'up':
            return (self.x, self.y + 1)
        else:  # down
            return (self.x, self.y - 1)

    def get_minable_positions_in_direction(self, direction: str) -> list[tuple[int, int]]:
        """Get mineable positions for a direction, in priority order."""
        if direction == 'left':
            return [(self.x - 1, self.y)]
        elif direction == 'right':
            return [(self.x + 1, self.y)]
        elif direction == 'up':
            return [(self.x, self.y + 1)]
        else:  # down
            return [(self.x, self.y - 1)]
