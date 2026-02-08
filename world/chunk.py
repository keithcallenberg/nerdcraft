"""Chunk storage for 16x16 block regions."""

from __future__ import annotations
from typing import List
from game.config import CHUNK_SIZE
from world.block import BlockType


class Chunk:
    """A 16x16 region of blocks."""

    def __init__(self, chunk_x: int, chunk_y: int):
        """Initialize an empty chunk at the given chunk coordinates."""
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        # 2D array of blocks [x][y], initialized to air
        self._blocks: list[list[BlockType]] = [
            [BlockType.AIR for _ in range(CHUNK_SIZE)]
            for _ in range(CHUNK_SIZE)
        ]

    def get_block(self, local_x: int, local_y: int) -> BlockType:
        """Get block at local coordinates (0-15, 0-15)."""
        if 0 <= local_x < CHUNK_SIZE and 0 <= local_y < CHUNK_SIZE:
            return self._blocks[local_x][local_y]
        return BlockType.AIR

    def set_block(self, local_x: int, local_y: int, block_type: BlockType) -> None:
        """Set block at local coordinates (0-15, 0-15)."""
        if 0 <= local_x < CHUNK_SIZE and 0 <= local_y < CHUNK_SIZE:
            self._blocks[local_x][local_y] = block_type

    @property
    def world_x(self) -> int:
        """Get world X coordinate of chunk's origin."""
        return self.chunk_x * CHUNK_SIZE

    @property
    def world_y(self) -> int:
        """Get world Y coordinate of chunk's origin."""
        return self.chunk_y * CHUNK_SIZE
