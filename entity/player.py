"""Player entity with position, velocity, and actions."""

from __future__ import annotations
from typing import Tuple
from util.vector import Vec2
from game.config import PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_SPEED, JUMP_VELOCITY


class Player:
    """The player entity."""

    def __init__(self, x: float = 0.0, y: float = 0.0):
        """Initialize player at given position."""
        self.position = Vec2(x, y)
        self.velocity = Vec2(0.0, 0.0)
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.on_ground = False
        self.facing_right = True  # Direction player is facing

    @property
    def x(self) -> float:
        return self.position.x

    @x.setter
    def x(self, value: float) -> None:
        self.position.x = value

    @property
    def y(self) -> float:
        return self.position.y

    @y.setter
    def y(self, value: float) -> None:
        self.position.y = value

    def move_left(self) -> None:
        """Start moving left."""
        self.velocity.x = -PLAYER_SPEED
        self.facing_right = False

    def move_right(self) -> None:
        """Start moving right."""
        self.velocity.x = PLAYER_SPEED
        self.facing_right = True

    def stop_horizontal(self) -> None:
        """Stop horizontal movement."""
        self.velocity.x = 0.0

    def jump(self) -> bool:
        """Attempt to jump. Returns True if successful."""
        if self.on_ground:
            self.velocity.y = JUMP_VELOCITY
            self.on_ground = False
            return True
        return False

    def get_aabb(self) -> tuple[float, float, float, float]:
        """Get axis-aligned bounding box (left, bottom, right, top)."""
        half_width = self.width / 2
        return (
            self.x - half_width,
            self.y,
            self.x + half_width,
            self.y + self.height
        )

    def get_block_in_front(self) -> tuple[int, int]:
        """Get the block coordinates in front of the player."""
        if self.facing_right:
            block_x = int(self.x + self.width / 2 + 0.5)
        else:
            block_x = int(self.x - self.width / 2 - 0.5)
        # Target block at player's mid-height
        block_y = int(self.y + self.height / 2)
        return (block_x, block_y)

    def get_block_below_front(self) -> tuple[int, int]:
        """Get the block coordinates below and in front of the player."""
        if self.facing_right:
            block_x = int(self.x + self.width / 2 + 0.5)
        else:
            block_x = int(self.x - self.width / 2 - 0.5)
        block_y = int(self.y)
        return (block_x, block_y)
