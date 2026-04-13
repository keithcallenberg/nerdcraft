"""World management with chunk-based storage."""

from __future__ import annotations
from config import GameConfig
from world.block import BlockType
from world.chunk import Chunk


class World:
    """Manages all chunks and provides world-coordinate block access."""

    def __init__(self):
        """Initialize an empty world."""
        self._chunks: dict[tuple[int, int], Chunk] = {}
        cfg = GameConfig.get()
        self.chunk_size = cfg.chunk_size
        self.world_height_chunks = cfg.world_height_chunks

    def _world_to_chunk(self, world_x: int, world_y: int) -> tuple[int, int, int, int]:
        """Convert world coordinates to chunk coordinates and local offsets."""
        chunk_x = world_x // self.chunk_size
        chunk_y = world_y // self.chunk_size
        local_x = world_x % self.chunk_size
        local_y = world_y % self.chunk_size
        return chunk_x, chunk_y, local_x, local_y

    def get_chunk(self, chunk_x: int, chunk_y: int) -> Chunk | None:
        """Get chunk at chunk coordinates, or None if not loaded."""
        return self._chunks.get((chunk_x, chunk_y))

    def get_or_create_chunk(self, chunk_x: int, chunk_y: int) -> Chunk:
        """Get chunk at chunk coordinates, creating if necessary."""
        key = (chunk_x, chunk_y)
        if key not in self._chunks:
            self._chunks[key] = Chunk(chunk_x, chunk_y, self.chunk_size)
        return self._chunks[key]

    def get_block(self, world_x: int, world_y: int) -> BlockType:
        """Get block at world coordinates."""
        # Out of bounds checks
        if world_y < 0:
            return BlockType.BEDROCK
        if world_y >= self.world_height_chunks * self.chunk_size:
            return BlockType.AIR

        chunk_x, chunk_y, local_x, local_y = self._world_to_chunk(world_x, world_y)
        chunk = self.get_chunk(chunk_x, chunk_y)
        if chunk is None:
            return BlockType.AIR
        return chunk.get_block(local_x, local_y)

    def set_block(self, world_x: int, world_y: int, block_type: BlockType) -> bool:
        """Set block at world coordinates. Returns True if successful."""
        if world_y < 0 or world_y >= self.world_height_chunks * self.chunk_size:
            return False

        chunk_x, chunk_y, local_x, local_y = self._world_to_chunk(world_x, world_y)
        chunk = self.get_or_create_chunk(chunk_x, chunk_y)
        chunk.set_block(local_x, local_y, block_type)
        return True

    def is_solid(self, world_x: int, world_y: int, entity=None) -> bool:
        """Check if block at world coordinates is solid for a given entity."""
        block = self.get_block(world_x, world_y)
        if block == BlockType.DOOR:
            from entity.player import Player
            return not isinstance(entity, Player)

        from world.block import is_solid
        return is_solid(block)

    def get_loaded_chunks(self) -> list[Chunk]:
        """Get all currently loaded chunks."""
        return list(self._chunks.values())

    def world_to_chunk_coords(self, world_x: int, world_y: int) -> tuple[int, int]:
        """Get chunk coordinates containing a world coordinate."""
        chunk_x, chunk_y, _, _ = self._world_to_chunk(world_x, world_y)
        return chunk_x, chunk_y

    def get_chunks_in_radius(self, center_x: int, center_y: int, radius_chunks: int) -> list[Chunk]:
        """Return loaded chunks within a chunk-radius of a world position."""
        cx, cy = self.world_to_chunk_coords(center_x, center_y)
        result: list[Chunk] = []
        for dx in range(-radius_chunks, radius_chunks + 1):
            for dy in range(-radius_chunks, radius_chunks + 1):
                chunk = self.get_chunk(cx + dx, cy + dy)
                if chunk is not None:
                    result.append(chunk)
        return result
