"""Procedural terrain generation with noise."""

from __future__ import annotations
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
from config import GameConfig
from world.block import BlockType
from world.world import World
from world.chunk import Chunk


@dataclass(frozen=True)
class TreeRules:
    """Procedural tree generation settings for a biome."""

    density: float
    trunk_block: BlockType
    leaf_block: BlockType
    cell_width: int
    x_margin: int
    x_jitter: int
    trunk_height_min: int
    trunk_height_max: int
    canopy_radius_min: int
    canopy_radius_max: int
    canopy_height_min: int
    canopy_height_max: int


@dataclass(frozen=True)
class ColumnFeatureRules:
    """Vertical column feature generation such as cactus."""

    block: BlockType
    requires_surface_block: BlockType | None
    spawn_mod: int
    height_min: int
    height_max: int


@dataclass(frozen=True)
class OreRule:
    """Data-driven ore generation rule."""

    block: BlockType
    min_depth: int
    threshold: float
    multiplier_key: str


@dataclass(frozen=True)
class BiomeRules:
    """Resolved biome generation rules with safe content-id fallbacks."""

    surface_block: BlockType
    subsurface_block: BlockType
    tree: TreeRules | None
    column_features: tuple[ColumnFeatureRules, ...]
    ore_multipliers: dict[str, float]
    ore_rules: tuple[OreRule, ...]
    mob_spawn_table: list[tuple[str, int]]
    surface_roughness: float
    biome_size_weight: float
    lake_frequency: float
    lake_fill_block: BlockType
    lake_bottom_block: BlockType
    cave_fill_block: BlockType


class WorldGenerator:
    """Generates procedural terrain using noise functions."""

    def __init__(self, seed: int | None = None):
        """Initialize generator with optional seed."""
        self.cfg = GameConfig.get()
        self.seed = seed if seed is not None else random.randint(0, 2**32 - 1)
        self._empty_block = BlockType[self.cfg.empty_block_id.upper()]
        self._boundary_block = BlockType[self.cfg.boundary_block_id.upper()]
        self._base_solid_block = BlockType[self.cfg.base_solid_block_id.upper()]
        self._rng = random.Random(self.seed)
        # Generate permutation table for noise
        self._perm = list(range(256))
        self._rng.shuffle(self._perm)
        self._perm = self._perm + self._perm  # Double for overflow

        # Biome map (second noise pass): sorted by config key for stable ordering
        self._biome_ids, self._biome_rules, self._biome_blend_fraction = self._load_biome_rules()
        self._rebuild_biome_ranges()

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

    def _to_block_type(self, block_name: str, fallback: BlockType) -> BlockType:
        """Resolve config block name to enum with fallback for unknown blocks."""
        try:
            return BlockType[block_name.upper()]
        except KeyError:
            return fallback

    @staticmethod
    def _range_bounds(raw_range, default_min: int, default_max: int) -> tuple[int, int]:
        if isinstance(raw_range, list) and len(raw_range) >= 2:
            try:
                low = int(raw_range[0])
                high = int(raw_range[1])
                if high < low:
                    low, high = high, low
                return (low, high)
            except (TypeError, ValueError):
                pass
        return (default_min, default_max)

    def _load_biome_rules(self) -> tuple[list[str], dict[str, BiomeRules], float]:
        """Load biome ids + generation rules from config/biomes.json."""
        config_path = Path(__file__).resolve().parent.parent / "config" / "biomes.json"
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            data = {}

        biomes = data.get("biomes", {})
        biome_blend_fraction = max(0.0, min(0.45, float(data.get("blend_fraction", 0.18))))
        biome_ids = sorted(biomes.keys())
        rules: dict[str, BiomeRules] = {}

        for biome_id in biome_ids:
            cfg = biomes.get(biome_id, {})
            surface = self._to_block_type(cfg.get("surface_block", "grass"), BlockType.GRASS)
            subsurface = self._to_block_type(cfg.get("subsurface_block", "dirt"), BlockType.DIRT)
            tree_cfg = cfg.get("tree", {})
            if not isinstance(tree_cfg, dict):
                tree_cfg = {}
            tree_density = max(0.0, min(1.0, float(tree_cfg.get("density", cfg.get("tree_density", 0.25)))))
            tree: TreeRules | None = None
            if tree_density > 0:
                trunk_height_min, trunk_height_max = self._range_bounds(tree_cfg.get("trunk_height"), 3, 7)
                canopy_radius_min, canopy_radius_max = self._range_bounds(tree_cfg.get("canopy_radius"), 2, 4)
                canopy_height_min, canopy_height_max = self._range_bounds(tree_cfg.get("canopy_height"), 2, 4)
                tree = TreeRules(
                    density=tree_density,
                    trunk_block=self._to_block_type(tree_cfg.get("trunk_block", "trunk"), self._base_solid_block),
                    leaf_block=self._to_block_type(tree_cfg.get("leaf_block", "leaves"), self._base_solid_block),
                    cell_width=max(4, int(tree_cfg.get("cell_width", 20))),
                    x_margin=max(0, int(tree_cfg.get("x_margin", 3))),
                    x_jitter=max(1, int(tree_cfg.get("x_jitter", 14))),
                    trunk_height_min=trunk_height_min,
                    trunk_height_max=trunk_height_max,
                    canopy_radius_min=canopy_radius_min,
                    canopy_radius_max=canopy_radius_max,
                    canopy_height_min=canopy_height_min,
                    canopy_height_max=canopy_height_max,
                )

            ore_cfg = cfg.get("ore_multipliers", {})
            multipliers = {str(key): float(value) for key, value in ore_cfg.items()}

            ore_rules_raw = cfg.get("ore_rules", [])
            if not isinstance(ore_rules_raw, list) or not ore_rules_raw:
                ore_rules_raw = [
                    {"block": "diamond_ore", "min_depth": 50, "threshold": 0.95, "multiplier": "diamond_ore"},
                    {"block": "gold_ore", "min_depth": 35, "threshold": 0.9, "multiplier": "gold_ore"},
                    {"block": "iron_ore", "min_depth": 20, "threshold": 0.85, "multiplier": "iron_ore"},
                    {"block": "coal_ore", "min_depth": 0, "threshold": 0.8, "multiplier": "coal_ore"},
                ]
            ore_rules: list[OreRule] = []
            for entry in ore_rules_raw:
                if not isinstance(entry, dict):
                    continue
                ore_rules.append(
                    OreRule(
                        block=self._to_block_type(str(entry.get("block", self.cfg.base_solid_block_id)), self._base_solid_block),
                        min_depth=max(0, int(entry.get("min_depth", 0))),
                        threshold=float(entry.get("threshold", 0.8)),
                        multiplier_key=str(entry.get("multiplier", entry.get("block", ""))).strip(),
                    )
                )

            column_features_raw = cfg.get("column_features", [])
            column_features: list[ColumnFeatureRules] = []
            if isinstance(column_features_raw, list):
                for entry in column_features_raw:
                    if not isinstance(entry, dict):
                        continue
                    height_min, height_max = self._range_bounds(entry.get("height"), 2, 3)
                    surface_req = entry.get("requires_surface_block")
                    column_features.append(
                        ColumnFeatureRules(
                            block=self._to_block_type(str(entry.get("block", self.cfg.base_solid_block_id)), self._base_solid_block),
                            requires_surface_block=(
                                self._to_block_type(str(surface_req), surface) if surface_req else None
                            ),
                            spawn_mod=max(1, int(entry.get("spawn_mod", 23))),
                            height_min=height_min,
                            height_max=height_max,
                        )
                    )

            spawn_table_cfg = cfg.get("mob_spawn_table", [])
            spawn_table: list[tuple[str, int]] = []
            for entry in spawn_table_cfg:
                mob_id = str(entry.get("mob", "")).strip()
                try:
                    weight = int(entry.get("weight", 0))
                except (TypeError, ValueError):
                    weight = 0
                if mob_id and weight > 0:
                    spawn_table.append((mob_id, weight))

            surface_roughness = max(0.0, float(cfg.get("surface_roughness", 1.0)))
            biome_size_weight = max(0.01, float(cfg.get("biome_size_weight", 1.0)))
            lake_frequency = max(0.0, min(1.0, float(cfg.get("lake_frequency", 0.0))))

            rules[biome_id] = BiomeRules(
                surface_block=surface,
                subsurface_block=subsurface,
                tree=tree,
                column_features=tuple(column_features),
                ore_multipliers=multipliers,
                ore_rules=tuple(ore_rules),
                mob_spawn_table=spawn_table,
                surface_roughness=surface_roughness,
                biome_size_weight=biome_size_weight,
                lake_frequency=lake_frequency,
                lake_fill_block=self._to_block_type(cfg.get("lake_fill_block", self.cfg.water_block_id), self._empty_block),
                lake_bottom_block=self._to_block_type(cfg.get("lake_bottom_block", self.cfg.base_solid_block_id), self._base_solid_block),
                cave_fill_block=self._to_block_type(cfg.get("cave_fill_block", self.cfg.water_block_id), self._empty_block),
            )

        if not biome_ids:
            biome_ids = ["forest"]
            rules = {
                "forest": BiomeRules(
                    surface_block=self._to_block_type("grass", self._base_solid_block),
                    subsurface_block=self._to_block_type("dirt", self._base_solid_block),
                    tree=TreeRules(0.25, self._to_block_type("trunk", self._base_solid_block), self._to_block_type("leaves", self._base_solid_block), 20, 3, 14, 3, 7, 2, 4, 2, 4),
                    column_features=(),
                    ore_multipliers={
                        "coal_ore": 1.0,
                        "iron_ore": 1.0,
                        "gold_ore": 1.0,
                        "diamond_ore": 1.0,
                    },
                    ore_rules=(
                        OreRule(self._to_block_type("diamond_ore", self._base_solid_block), 50, 0.95, "diamond_ore"),
                        OreRule(self._to_block_type("gold_ore", self._base_solid_block), 35, 0.9, "gold_ore"),
                        OreRule(self._to_block_type("iron_ore", self._base_solid_block), 20, 0.85, "iron_ore"),
                        OreRule(self._to_block_type("coal_ore", self._base_solid_block), 0, 0.8, "coal_ore"),
                    ),
                    mob_spawn_table=[],
                    surface_roughness=1.0,
                    biome_size_weight=1.0,
                    lake_frequency=0.0,
                    lake_fill_block=self._to_block_type(self.cfg.water_block_id, self._empty_block),
                    lake_bottom_block=self._base_solid_block,
                    cave_fill_block=self._to_block_type(self.cfg.water_block_id, self._empty_block),
                )
            }

        return biome_ids, rules, biome_blend_fraction

    def _rebuild_biome_ranges(self) -> None:
        """Build cumulative weighted biome ranges for deterministic lookup/blending."""
        self._biome_ranges: list[tuple[str, float, float]] = []
        start = 0.0
        for biome_id in self._biome_ids:
            w = max(0.01, self._biome_rules[biome_id].biome_size_weight)
            end = start + w
            self._biome_ranges.append((biome_id, start, end))
            start = end
        self._biome_total_weight = max(0.01, start)

    def _biome_target(self, world_x: int) -> float:
        """Map world x into weighted biome axis position."""
        biome_noise = self._fbm1d(world_x * 0.004 + 1337.0, octaves=3, persistence=0.55)
        normalized = (biome_noise + 1.0) / 2.0
        normalized = max(0.0, min(0.999999, normalized))
        return normalized * self._biome_total_weight

    def _primary_biome_index(self, target: float) -> int:
        for i, (_, start, end) in enumerate(self._biome_ranges):
            if start <= target < end:
                return i
        return max(0, len(self._biome_ranges) - 1)

    def _biome_blend(self, world_x: int) -> list[tuple[BiomeRules, float]]:
        """Return one or two biome rules with weights for smooth transitions."""
        if not self._biome_ranges:
            fallback = self._biome_rules[self._biome_ids[0]]
            return [(fallback, 1.0)]

        target = self._biome_target(world_x)
        idx = self._primary_biome_index(target)
        biome_id, start, end = self._biome_ranges[idx]
        width = max(0.0001, end - start)
        t = (target - start) / width

        blend = self._biome_blend_fraction
        primary = self._biome_rules[biome_id]

        # Blend near left edge with previous biome.
        if t < blend and len(self._biome_ranges) > 1:
            prev_id = self._biome_ranges[(idx - 1) % len(self._biome_ranges)][0]
            w_prev = (blend - t) / blend
            w_primary = 1.0 - w_prev
            return [(primary, w_primary), (self._biome_rules[prev_id], w_prev)]

        # Blend near right edge with next biome.
        if t > (1.0 - blend) and len(self._biome_ranges) > 1:
            next_id = self._biome_ranges[(idx + 1) % len(self._biome_ranges)][0]
            w_next = (t - (1.0 - blend)) / blend
            w_primary = 1.0 - w_next
            return [(primary, w_primary), (self._biome_rules[next_id], w_next)]

        return [(primary, 1.0)]

    def _choose_blended_block(
        self,
        world_x: int,
        world_y: int,
        options: list[tuple[BlockType, float]],
    ) -> BlockType:
        """Deterministically choose a block from weighted biome options."""
        cleaned = [(b, max(0.0, w)) for b, w in options if w > 0]
        if not cleaned:
            return self._base_solid_block

        total = sum(w for _, w in cleaned)
        if total <= 0:
            return cleaned[0][0]

        pick_noise = self._noise2d(world_x * 0.17 + 911.0, world_y * 0.19 + 577.0)
        target = pick_noise * total

        cumulative = 0.0
        for block, weight in cleaned:
            cumulative += weight
            if target <= cumulative:
                return block

        return cleaned[-1][0]

    def get_biome_id(self, world_x: int) -> str:
        """Get primary biome id for an X coordinate."""
        if not self._biome_ids:
            return "forest"

        target = self._biome_target(world_x)
        idx = self._primary_biome_index(target)
        return self._biome_ranges[idx][0]

    def _get_biome_rules(self, world_x: int) -> BiomeRules:
        """Return generation rules for the biome at this x coordinate."""
        biome_id = self.get_biome_id(world_x)
        return self._biome_rules.get(biome_id, self._biome_rules[self._biome_ids[0]])

    def get_surface_height(self, world_x: int) -> int:
        """Get terrain surface height at given X coordinate."""
        # Use multiple octaves for varied terrain
        noise = self._fbm1d(world_x * 0.02, octaves=4)

        # Blend roughness near biome boundaries for smoother transitions.
        roughness = 0.0
        for rules, weight in self._biome_blend(world_x):
            roughness += rules.surface_roughness * weight

        # `surface_roughness` controls how level a biome is.
        # 1.0 = current default variation, lower = flatter terrain.
        base_amplitude = 15
        height_variation = int(noise * base_amplitude * roughness)
        return self.cfg.sea_level + height_variation

    def _get_tree_for_cell(self, cell_index: int) -> tuple | None:
        """Get tree properties for a cell, or None if no tree spawns.

        Divides the world x-axis into cells of width 20. Each cell has a
        chance of containing one tree with randomised position and size.

        Returns (tree_x, trunk_height, canopy_radius, canopy_height).
        """
        h = self._perm[(cell_index * 7 + 13) & 255]
        cell_width = 20
        center_x = cell_index * cell_width + (cell_width // 2)
        biome = self._get_biome_rules(center_x)
        tree = biome.tree
        if tree is None:
            return None
        cell_width = tree.cell_width
        center_x = cell_index * cell_width + (cell_width // 2)
        biome = self._get_biome_rules(center_x)
        tree = biome.tree
        if tree is None or (h / 255.0) > tree.density:
            return None

        # Do not spawn trees where the local surface column is part of a lake.
        center_surface = self.get_surface_height(center_x)
        if self._lake_depth_at(center_x, center_surface, biome) > 0:
            return None

        cell_start = cell_index * tree.cell_width
        # Jitter x within the cell, leaving a margin for canopy overhang
        jitter = self._perm[(cell_index * 13 + 37) & 255] % tree.x_jitter
        tree_x = cell_start + jitter + tree.x_margin

        trunk_span = max(1, tree.trunk_height_max - tree.trunk_height_min + 1)
        canopy_radius_span = max(1, tree.canopy_radius_max - tree.canopy_radius_min + 1)
        canopy_height_span = max(1, tree.canopy_height_max - tree.canopy_height_min + 1)
        trunk_height = tree.trunk_height_min + (self._perm[(cell_index * 19 + 73) & 255] % trunk_span)
        canopy_radius = tree.canopy_radius_min + (self._perm[(cell_index * 23 + 97) & 255] % canopy_radius_span)
        canopy_height = tree.canopy_height_min + (self._perm[(cell_index * 29 + 113) & 255] % canopy_height_span)
        return (tree_x, trunk_height, canopy_radius, canopy_height, tree.trunk_block, tree.leaf_block, tree.cell_width)

    def _check_tree_block(self, world_x: int, world_y: int) -> BlockType | None:
        """Return TRUNK / LEAVES if this position belongs to a tree, else None."""
        biome = self._get_biome_rules(world_x)
        cell_width = biome.tree.cell_width if biome.tree is not None else 20
        cell = world_x // cell_width

        for check_cell in range(cell - 1, cell + 2):
            tree = self._get_tree_for_cell(check_cell)
            if tree is None:
                continue

            tree_x, trunk_height, canopy_radius, canopy_height, trunk_block, leaf_block, _ = tree
            tree_surface = self.get_surface_height(tree_x)

            # Trunk — single column rising from the surface
            if world_x == tree_x and tree_surface < world_y <= tree_surface + trunk_height:
                return trunk_block

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
                    return leaf_block

        return None

    def generate_chunk(self, chunk: Chunk) -> None:
        """Generate terrain for a chunk."""
        for local_x in range(self.cfg.chunk_size):
            world_x = chunk.world_x + local_x
            surface_height = self.get_surface_height(world_x)

            for local_y in range(self.cfg.chunk_size):
                world_y = chunk.world_y + local_y
                block_type = self._get_block_at(world_x, world_y, surface_height)
                chunk.set_block(local_x, local_y, block_type)

    def _lake_depth_at(self, world_x: int, surface_height: int, biome: BiomeRules) -> int:
        """Return lake depth at a surface column, or 0 if no lake spawns here."""
        if biome.lake_frequency <= 0:
            return 0

        coarse = self._noise1d(world_x * 0.035 + 2048.0)
        threshold = 0.72 - (0.32 * biome.lake_frequency)
        if coarse < threshold:
            return 0

        shape = self._noise1d(world_x * 0.09 + 4096.0)
        depth = 1 + int(max(0.0, (coarse - threshold) * 10.0) + max(0.0, shape + 0.2) * 2.0)
        return min(5, max(1, depth))

    def _get_block_at(self, world_x: int, world_y: int, surface_height: int) -> BlockType:
        """Determine block type at given world coordinates."""
        biome = self._get_biome_rules(world_x)
        biome_mix = self._biome_blend(world_x)

        # Trees (only above the local surface so they don't poke into terrain)
        if world_y > surface_height:
            tree_block = self._check_tree_block(world_x, world_y)
            if tree_block is not None:
                return tree_block

            for feature in biome.column_features:
                if (
                    feature.requires_surface_block is not None
                    and biome.surface_block != feature.requires_surface_block
                ):
                    continue
                feature_hash = self._perm[(world_x * 5 + 41) & 255]
                if feature_hash % feature.spawn_mod != 0:
                    continue
                height_span = max(1, feature.height_max - feature.height_min + 1)
                feature_height = feature.height_min + (self._perm[(world_x * 7 + 89) & 255] % height_span)
                if surface_height < world_y <= surface_height + feature_height:
                    return feature.block

        # Bedrock at bottom
        if world_y <= 0:
            return self._boundary_block

        # Air above surface
        if world_y > surface_height:
            return self._empty_block

        # Depth below surface
        depth = surface_height - world_y

        # Surface lakes: carve shallow depressions filled with water based on biome frequency.
        lake_depth = self._lake_depth_at(world_x, surface_height, biome)
        if lake_depth > 0:
            lake_bottom_y = surface_height - lake_depth
            if world_y == lake_bottom_y:
                return biome.lake_bottom_block
            if lake_bottom_y < world_y <= surface_height:
                return biome.lake_fill_block

        # Biome surface block (blend materials near biome borders)
        if depth == 0:
            return self._choose_blended_block(
                world_x,
                world_y,
                [(rules.surface_block, weight) for rules, weight in biome_mix],
            )

        # Biome subsurface layer (blend materials near biome borders)
        if depth < self.cfg.dirt_depth:
            return self._choose_blended_block(
                world_x,
                world_y,
                [(rules.subsurface_block, weight) for rules, weight in biome_mix],
            )

        # Check for caves
        cave_noise = self._noise2d(world_x * 0.1, world_y * 0.1)
        if cave_noise > 0.7 and depth > self.cfg.dirt_depth + 2:
            return biome.cave_fill_block

        # Stone with biome-tuned ore generation
        if depth >= self.cfg.stone_depth:
            return self._generate_ore(world_x, world_y, depth, biome)

        # Transition zone (mostly dirt/subsurface, some stone)
        if depth >= self.cfg.dirt_depth:
            return self._base_solid_block

        return biome.subsurface_block

    def _generate_ore(self, world_x: int, world_y: int, depth: int, biome: BiomeRules) -> BlockType:
        """Generate ore blocks based on depth and biome ore multipliers."""
        ore_noise = self._noise2d(world_x * 0.3 + 1000, world_y * 0.3)

        for rule in biome.ore_rules:
            mult = max(0.0, biome.ore_multipliers.get(rule.multiplier_key, 1.0))
            if depth > rule.min_depth and ore_noise > (rule.threshold - 0.05 * max(0.0, mult - 1.0)):
                return rule.block

        return self._base_solid_block

    def generate_world(self, world: World, progress_callback=None) -> None:
        """Generate all chunks in the world."""
        total = self.cfg.world_width_chunks * self.cfg.world_height_chunks
        done = 0
        for chunk_x in range(self.cfg.world_width_chunks):
            for chunk_y in range(self.cfg.world_height_chunks):
                chunk = world.get_or_create_chunk(chunk_x, chunk_y)
                self.generate_chunk(chunk)
                done += 1
                if progress_callback is not None:
                    progress_callback(done, total)

    def _weighted_pick_mob_id(self, weighted_ids: list[tuple[str, int]], pick: int) -> str | None:
        """Pick a mob id from (mob_id, weight) pairs using a deterministic integer pick."""
        if not weighted_ids:
            return None
        total_weight = sum(weight for _, weight in weighted_ids)
        if total_weight <= 0:
            return None

        pick_mod = pick % total_weight
        cumulative = 0
        for mob_id, weight in weighted_ids:
            cumulative += weight
            if pick_mod < cumulative:
                return mob_id
        return weighted_ids[-1][0]

    def _biome_spawn_candidates(
        self,
        world_x: int,
        allowed_mob_ids: set[str],
    ) -> tuple[list[tuple[str, int]], bool]:
        """Return filtered biome spawn entries and whether the biome table is explicitly configured."""
        biome_id = self.get_biome_id(world_x)
        biome_rules = self._biome_rules.get(biome_id)
        if biome_rules is None:
            return ([], False)

        has_biome_table = len(biome_rules.mob_spawn_table) > 0
        candidates = [
            (mob_id, weight)
            for mob_id, weight in biome_rules.mob_spawn_table
            if mob_id in allowed_mob_ids and weight > 0
        ]
        return (candidates, has_biome_table)

    def spawn_mobs(self, world: World) -> list:
        """Spawn daytime/default surface mobs using biome-aware weighted tables."""
        from entity.mob import Mob
        from entity.mob_registry import MobRegistry

        registry = MobRegistry.get()
        surface_pool = registry.surface_mobs()
        if not surface_pool:
            return []

        allowed_surface_ids = {d.mob_id for d in surface_pool}
        global_weights = [(d.mob_id, d.spawn.weight) for d in surface_pool if d.spawn.weight > 0]

        mobs = []
        world_width = self.cfg.world_width_chunks * self.cfg.chunk_size
        for sample_x in range(0, world_width, 40):
            # Use perm table for deterministic spawning (~40% chance)
            h = self._perm[(sample_x * 11 + 53) & 255]
            if h % 100 < 40:
                surface_y = self.get_surface_height(sample_x)
                # Prefer biome table; fallback to global surface weights if table is empty/invalid.
                biome_weights, has_biome_table = self._biome_spawn_candidates(sample_x, allowed_surface_ids)
                candidates = biome_weights if has_biome_table else global_weights
                mob_id = self._weighted_pick_mob_id(candidates, self._perm[(sample_x * 7 + 97) & 255])
                if mob_id is None:
                    continue
                mob = Mob(sample_x, surface_y + 1, mob_id=mob_id)
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

        allowed_night_ids = {d.mob_id for d in night_pool}
        global_weights = [(d.mob_id, d.spawn.weight) for d in night_pool if d.spawn.weight > 0]
        occupied = occupied_positions or set()

        world_width = self.cfg.world_width_chunks * self.cfg.chunk_size
        for _ in range(6):
            sample_x = self._rng.randrange(0, world_width)
            surface_y = self.get_surface_height(sample_x)
            pos = (sample_x, surface_y + 1)
            if pos in occupied:
                continue

            biome_weights, has_biome_table = self._biome_spawn_candidates(sample_x, allowed_night_ids)
            candidates = biome_weights if has_biome_table else global_weights
            mob_id = self._weighted_pick_mob_id(candidates, self._rng.randrange(0, 10_000))
            if mob_id is None:
                continue

            return Mob(sample_x, surface_y + 1, mob_id=mob_id)

        return None

    def get_spawn_position(self) -> tuple[int, int]:
        """Get a valid spawn position for the player."""
        spawn_x = (self.cfg.world_width_chunks * self.cfg.chunk_size) // 2
        surface_y = self.get_surface_height(spawn_x)
        # Spawn player just above the surface
        return (spawn_x, surface_y + 2)
