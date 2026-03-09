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

    def _get_tree_for_cell(self, cell_index: int) -> tuple | None:
        """Get tree properties for a cell, or None if no tree spawns.

        Divides the world x-axis into cells of width 20. Each cell has a
        chance of containing one tree with randomised position and size.

        Returns (tree_x, trunk_height, canopy_radius, canopy_height).
        """
        h = self._perm[(cell_index * 7 + 13) & 255]
        # ~25 % chance of skipping a tree
        if h < 64:
            return None

        cell_start = cell_index * 20
        # Jitter x within the cell, leaving a margin for canopy overhang
        jitter = self._perm[(cell_index * 13 + 37) & 255] % 14
        tree_x = cell_start + jitter + 3

        trunk_height = 3 + self._perm[(cell_index * 19 + 73) & 255] % 5   # 3-7
        canopy_radius = 2 + self._perm[(cell_index * 23 + 97) & 255] % 3  # 2-4
        canopy_height = 2 + self._perm[(cell_index * 29 + 113) & 255] % 3 # 2-4
        return (tree_x, trunk_height, canopy_radius, canopy_height)

    def _check_tree_block(self, world_x: int, world_y: int) -> BlockType | None:
        """Return TRUNK / LEAVES if this position belongs to a tree, else None."""
        cell = world_x // 20

        for check_cell in range(cell - 1, cell + 2):
            tree = self._get_tree_for_cell(check_cell)
            if tree is None:
                continue

            tree_x, trunk_height, canopy_radius, canopy_height = tree
            tree_surface = self.get_surface_height(tree_x)

            # Trunk — single column rising from the surface
            if world_x == tree_x and tree_surface < world_y <= tree_surface + trunk_height:
                return BlockType.TRUNK

            # Canopy — sits on top of the trunk
            canopy_base = tree_surface + trunk_height
            canopy_top = canopy_base + canopy_height
            dx = abs(world_x - tree_x)

            if dx <= canopy_radius and canopy_base < world_y <= canopy_top:
                # Fraction through the canopy (0 at bottom, 1 at top)
                t = (world_y - canopy_base) / canopy_height

                # Parabolic profile peaking in the lower-middle of the canopy
                t_adj = (t - 0.4) * 2.0
                shape = max(1.0 - t_adj * t_adj, 0.3)
                effective_radius = canopy_radius * shape

                # Per-block noise for irregular edges
                leaf_hash = self._perm[(world_x * 3 + world_y * 7) & 255] / 255.0
                edge_adjust = (leaf_hash - 0.5) * 1.5

                if dx <= effective_radius + edge_adjust:
                    return BlockType.LEAVES

        return None

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
        # Trees (only above the local surface so they don't poke into terrain)
        if world_y > surface_height:
            tree_block = self._check_tree_block(world_x, world_y)
            if tree_block is not None:
                return tree_block

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

    def spawn_mobs(self, world: World) -> list:
        """Spawn daytime/default surface mobs using weighted selection."""
        from entity.mob import Mob
        from entity.mob_registry import MobRegistry

        registry = MobRegistry.get()
        surface_pool = registry.surface_mobs()
        if not surface_pool:
            return []

        # Build a weighted list for selection
        weights = [d.spawn.weight for d in surface_pool]
        total_weight = sum(weights)

        mobs = []
        world_width = WORLD_WIDTH_CHUNKS * CHUNK_SIZE
        for sample_x in range(0, world_width, 40):
            # Use perm table for deterministic spawning (~40% chance)
            h = self._perm[(sample_x * 11 + 53) & 255]
            if h % 100 < 40:
                surface_y = self.get_surface_height(sample_x)
                # Pick mob type via weighted selection using perm table
                pick = self._perm[(sample_x * 7 + 97) & 255] % total_weight
                cumulative = 0
                chosen_def = surface_pool[0]
                for defn, w in zip(surface_pool, weights):
                    cumulative += w
                    if pick < cumulative:
                        chosen_def = defn
                        break
                mob = Mob(sample_x, surface_y + 1, mob_id=chosen_def.mob_id)
                mobs.append(mob)
        return mobs

    def spawn_night_hostile(
        self,
        world: World,
        occupied_positions: set[tuple[int, int]] | None = None,
    ):
        """Spawn one night-only hostile surface mob, if possible."""
        from entity.mob import Mob
        from entity.mob_registry import MobRegistry

        registry = MobRegistry.get()
        night_pool = [
            d for d in registry.all_defs()
            if d.hostile and d.spawn.surface and d.spawn.night_only
        ]
        if not night_pool:
            return None

        weights = [d.spawn.weight for d in night_pool]
        total_weight = sum(weights)
        occupied = occupied_positions or set()

        world_width = WORLD_WIDTH_CHUNKS * CHUNK_SIZE
        for _ in range(6):
            sample_x = self._rng.randrange(0, world_width)
            surface_y = self.get_surface_height(sample_x)
            pos = (sample_x, surface_y + 1)
            if pos in occupied:
                continue

            pick = self._rng.randrange(total_weight)
            cumulative = 0
            chosen_def = night_pool[0]
            for defn, w in zip(night_pool, weights):
                cumulative += w
                if pick < cumulative:
                    chosen_def = defn
                    break

            return Mob(sample_x, surface_y + 1, mob_id=chosen_def.mob_id)

        return None

    def get_spawn_position(self) -> tuple[int, int]:
        """Get a valid spawn position for the player."""
        spawn_x = (WORLD_WIDTH_CHUNKS * CHUNK_SIZE) // 2
        surface_y = self.get_surface_height(spawn_x)
        # Spawn player just above the surface
        return (spawn_x, surface_y + 2)
