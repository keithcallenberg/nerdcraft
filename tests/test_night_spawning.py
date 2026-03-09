"""Tests for night-only hostile spawning rules."""

from __future__ import annotations

import unittest

from world.generator import WorldGenerator
from world.world import World


class NightSpawningTests(unittest.TestCase):
    def test_spawn_night_hostile_uses_night_only_surface_hostiles(self) -> None:
        generator = WorldGenerator(seed=123)
        world = World()

        # Use an empty occupied set to allow spawning.
        mob = generator.spawn_night_hostile(world, occupied_positions=set())

        self.assertIsNotNone(mob)
        assert mob is not None
        self.assertTrue(mob.hostile)
        self.assertIn(mob.mob_id, {"zombie", "skeleton"})


if __name__ == "__main__":
    unittest.main()
