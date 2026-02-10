"""Camera viewport that follows the player."""

from __future__ import annotations
from typing import Tuple
from entity.player import Player


class Camera:
    """Viewport that follows the player."""

    def __init__(self, width: int, height: int):
        """Initialize camera with viewport size in characters."""
        self.width = width
        self.height = height
        self.x = 0.0  # World X of viewport left edge
        self.y = 0.0  # World Y of viewport bottom edge

    def update(self, player: Player) -> None:
        """Update camera to follow player, centering on them."""
        # Center camera on player (player occupies a single cell)
        target_x = player.x - self.width / 2
        target_y = player.y - self.height / 2

        # Smooth following (lerp)
        lerp_factor = 0.15
        self.x += (target_x - self.x) * lerp_factor
        self.y += (target_y - self.y) * lerp_factor

    def world_to_screen(self, world_x: float, world_y: float) -> tuple[int, int]:
        """Convert world coordinates to screen coordinates.

        Returns (col, row) where row 0 is top of screen.
        Y is flipped because world Y is up, but screen Y is down.
        """
        col = world_x - int(self.x)
        # Flip Y: world Y increases upward, screen row increases downward
        row = int(self.height - 1 - (world_y - self.y))
        return (col, row)

    def screen_to_world(self, col: int, row: int) -> tuple[int, int]:
        """Convert screen coordinates to world coordinates."""
        world_x = int(col + self.x)
        world_y = int((self.height - 1 - row) + self.y)
        return (world_x, world_y)

    def is_visible(self, world_x: int, world_y: int) -> bool:
        """Check if world coordinate is visible on screen."""
        col, row = self.world_to_screen(world_x, world_y)
        return 0 <= col < self.width and 0 <= row < self.height
