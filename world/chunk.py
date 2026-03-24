"""Chunk storage for configurable block regions."""

from __future__ import annotations
from world.block import BlockType
from config import GameConfig


class Chunk:
    """A chunk region of blocks (size from config)."""

    def __init__(self, chunk_x: int, chunk_y: int, chunk_size: int | None = None):
        """Initialize an empty chunk at the given chunk coordinates."""
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.chunk_size = chunk_size if chunk_size is not None else GameConfig.get().chunk_size
        # 2D array of blocks [x][y], initialized to air
        self._blocks: list[list[BlockType]] = [
            [BlockType.AIR for _ in range(self.chunk_size)]
            for _ in range(self.chunk_size)
        ]

    def get_block(self, local_x: int, local_y: int) -> BlockType:
        """Get block at local coordinates."""
        if 0 <= local_x < self.chunk_size and 0 <= local_y < self.chunk_size:
            return self._blocks[local_x][local_y]
        return BlockType.AIR

    def set_block(self, local_x: int, local_y: int, block_type: BlockType) -> None:
        """Set block at local coordinates."""
        if 0 <= local_x < self.chunk_size and 0 <= local_y < self.chunk_size:
            self._blocks[local_x][local_y] = block_type

    @property
    def world_x(self) -> int:
        """Get world X coordinate of chunk's origin."""
        return self.chunk_x * self.chunk_size

    @property
    def world_y(self) -> int:
        """Get world Y coordinate of chunk's origin."""
        return self.chunk_y * self.chunk_size
