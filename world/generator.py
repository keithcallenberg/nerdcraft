"""Procedural terrain generation with noise."""

from __future__ import annotations
import math
import random
from typing import Optional, Tuple
from game.config import (
    CHUNK_SIZE, WORLD_WIDTH_CHUNKS, WORLD_HEIGHT_CHUNKS,
    SEA_LEVEL, DIRT_DEPTH, STONE_DEPTH
)
from world.block import BlockType
from world.world import World
from world.chunk import Chunk


class WorldGenerator:
    """Generates procedural terrain using noise functions."""

    def __init__(self, seed: int | None = None):
        """Initialize generator with optional seed."""
        self.seed = seed if seed is not None else random.randint(0, 2**32 - 1)
        self._rng = random.Random(self.seed)
        # Generate permutation table for noise
        self._perm = list(range(256))
        self._rng.shuffle(self._perm)
        self._perm = self._perm + self._perm  # Double for overflow

    def _noise1d(self, x: float) -> float:
        """Simple 1D value noise for terrain height."""
        x0 = int(math.floor(x)) & 255
        x1 = (x0 + 1) & 255
        t = x - math.floor(x)
        # Smooth interpolation
        t = t * t * (3 - 2 * t)
        # Get random values from permutation table
        n0 = (self._perm[x0] / 255.0) * 2 - 1
        n1 = (self._perm[x1] / 255.0) * 2 - 1
        return n0 + t * (n1 - n0)

    def _noise2d(self, x: float, y: float) -> float:
        """Simple 2D value noise for caves and ores."""
        x0 = int(math.floor(x)) & 255
        y0 = int(math.floor(y)) & 255
        x1 = (x0 + 1) & 255
        y1 = (y0 + 1) & 255

        tx = x - math.floor(x)
        ty = y - math.floor(y)
        tx = tx * tx * (3 - 2 * tx)
        ty = ty * ty * (3 - 2 * ty)

        n00 = self._perm[self._perm[x0] + y0] / 255.0
        n01 = self._perm[self._perm[x0] + y1] / 255.0
        n10 = self._perm[self._perm[x1] + y0] / 255.0
        n11 = self._perm[self._perm[x1] + y1] / 255.0

        nx0 = n00 + tx * (n10 - n00)
        nx1 = n01 + tx * (n11 - n01)
        return nx0 + ty * (nx1 - nx0)

    def _fbm1d(self, x: float, octaves: int = 4, persistence: float = 0.5) -> float:
        """Fractal Brownian Motion for more natural terrain."""
        total = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_value = 0.0

        for _ in range(octaves):
            total += self._noise1d(x * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= 2

        return total / max_value

    def get_surface_height(self, world_x: int) -> int:
        """Get terrain surface height at given X coordinate."""
        # Use multiple octaves for varied terrain
        noise = self._fbm1d(world_x * 0.02, octaves=4)
        # Map noise to height variation around sea level
        height_variation = int(noise * 15)
        return SEA_LEVEL + height_variation

    def generate_chunk(self, chunk: Chunk) -> None:
        """Generate terrain for a chunk."""
        for local_x in range(CHUNK_SIZE):
            world_x = chunk.world_x + local_x
            surface_height = self.get_surface_height(world_x)

            for local_y in range(CHUNK_SIZE):
                world_y = chunk.world_y + local_y
                block_type = self._get_block_at(world_x, world_y, surface_height)
                chunk.set_block(local_x, local_y, block_type)

    def _get_block_at(self, world_x: int, world_y: int, surface_height: int) -> BlockType:
        """Determine block type at given world coordinates."""
	    # Trees of height 4 every 25 columns
        if world_y > surface_height and world_x % 25 == 0 and world_y < surface_height + 5:
            return BlockType.TRUNK
        
        # Leaves for trees
        if world_y > surface_height + 4 and world_y < surface_height + 7:
            if world_x % 25 < 3 or world_x % 25 > 22:
                return BlockType.LEAVES

        # Bedrock at bottom
        if world_y <= 0:
            return BlockType.BEDROCK

        # Air above surface
        if world_y > surface_height:
            return BlockType.AIR

        # Depth below surface
        depth = surface_height - world_y

        # Grass at surface
        if depth == 0:
            return BlockType.GRASS

        # Dirt layer
        if depth < DIRT_DEPTH:
            return BlockType.DIRT

        # Check for caves
        cave_noise = self._noise2d(world_x * 0.1, world_y * 0.1)
        if cave_noise > 0.7 and depth > DIRT_DEPTH + 2:
            return BlockType.WATER

        # Stone with ore generation
        if depth >= STONE_DEPTH:
            return self._generate_ore(world_x, world_y, depth)

        # Transition zone (mostly dirt, some stone)
        if depth >= DIRT_DEPTH:
            return BlockType.STONE

        return BlockType.DIRT

    def _generate_ore(self, world_x: int, world_y: int, depth: int) -> BlockType:
        """Generate ore blocks based on depth and noise."""
        ore_noise = self._noise2d(world_x * 0.3 + 1000, world_y * 0.3)

        # Diamond (deep and rare)
        if depth > 50 and ore_noise > 0.95:
            return BlockType.DIAMOND_ORE

        # Gold (medium-deep)
        if depth > 35 and ore_noise > 0.9:
            return BlockType.GOLD_ORE

        # Iron (medium depth)
        if depth > 20 and ore_noise > 0.85:
            return BlockType.IRON_ORE

        # Coal (common, any depth)
        if ore_noise > 0.8:
            return BlockType.COAL_ORE

        return BlockType.STONE

    def generate_world(self, world: World) -> None:
        """Generate all chunks in the world."""
        for chunk_x in range(WORLD_WIDTH_CHUNKS):
            for chunk_y in range(WORLD_HEIGHT_CHUNKS):
                chunk = world.get_or_create_chunk(chunk_x, chunk_y)
                self.generate_chunk(chunk)

    def get_spawn_position(self) -> tuple[float, float]:
        """Get a valid spawn position for the player."""
        spawn_x = (WORLD_WIDTH_CHUNKS * CHUNK_SIZE) // 2
        surface_y = self.get_surface_height(spawn_x)
        # Spawn player just above the surface
        return (float(spawn_x), float(surface_y + 10))
