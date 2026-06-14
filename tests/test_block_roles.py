"""Tests for JSON-defined block tags and role-driven behavior."""

from __future__ import annotations

import unittest

from entity.player import Player
from world.block import BlockType, has_tag
from world.world import World


class BlockRoleTests(unittest.TestCase):
    def test_block_tags_loaded_from_json(self) -> None:
        self.assertTrue(has_tag(BlockType.WATER, "liquid"))
        self.assertTrue(has_tag(BlockType.AIR, "replaceable"))
        self.assertTrue(has_tag(BlockType.DOOR, "player_passable"))

    def test_player_passable_blocks_respect_tag(self) -> None:
        world = World()
        player = Player()
        world.set_block(1, 1, BlockType.DOOR)
        self.assertFalse(world.is_solid(1, 1, entity=player))
        self.assertTrue(world.is_solid(1, 1, entity=object()))


if __name__ == "__main__":
    unittest.main()
