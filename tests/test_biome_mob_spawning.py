"""Tests for biome-specific mob spawn tables."""

from __future__ import annotations

import unittest

from entity.mob_registry import MobRegistry
from world.generator import WorldGenerator


class BiomeMobSpawningTests(unittest.TestCase):
    def test_desert_daytime_has_no_surface_spawns_from_table(self) -> None:
        generator = WorldGenerator(seed=42)
        registry = MobRegistry.get()

        allowed_surface_ids = {d.mob_id for d in registry.surface_mobs()}
        desert_cfg = generator._biome_rules["desert"].mob_spawn_table
        filtered = [(mob_id, w) for mob_id, w in desert_cfg if mob_id in allowed_surface_ids]

        self.assertEqual(filtered, [])

    def test_forest_daytime_prefers_cow_from_biome_table(self) -> None:
        generator = WorldGenerator(seed=42)
        registry = MobRegistry.get()

        allowed_surface_ids = {d.mob_id for d in registry.surface_mobs()}
        forest_cfg = generator._biome_rules["forest"].mob_spawn_table
        filtered = [(mob_id, w) for mob_id, w in forest_cfg if mob_id in allowed_surface_ids]

        self.assertEqual(filtered, [("cow", 12)])


if __name__ == "__main__":
    unittest.main()
