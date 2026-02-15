"""Camera viewport that follows the player."""

from __future__ import annotations
from entity.player import Player


class Camera:
    """Viewport that follows the player on the integer grid."""

    def __init__(self, width: int, height: int):
        """Initialize camera with viewport size in characters."""
        self.width = width
        self.height = height
        self.x = 0  # World X of viewport left edge
        self.y = 0  # World Y of viewport bottom edge

    def update(self, player: Player) -> None:
        """Snap camera to center on the player."""
        self.x = player.x - self.width // 2
        self.y = player.y - self.height // 2

    def world_to_screen(self, world_x: int, world_y: int) -> tuple[int, int]:
        """Convert world coordinates to screen coordinates.

        Returns (col, row) where row 0 is top of screen.
        Y is flipped because world Y is up, but screen Y is down.
        """
        col = world_x - self.x
        row = self.height - 1 - (world_y - self.y)
        return (col, row)

    def screen_to_world(self, col: int, row: int) -> tuple[int, int]:
        """Convert screen coordinates to world coordinates."""
        world_x = col + self.x
        world_y = (self.height - 1 - row) + self.y
        return (world_x, world_y)

    def is_visible(self, world_x: int, world_y: int) -> bool:
        """Check if world coordinate is visible on screen."""
        col, row = self.world_to_screen(world_x, world_y)
        return 0 <= col < self.width and 0 <= row < self.height
