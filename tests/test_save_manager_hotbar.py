from __future__ import annotations

import tempfile
import unittest

from entity.item import ItemType
from entity.player import Player
from world.block import BlockType
from world.save import SaveManager
from world.world import World


class SaveManagerHotbarTests(unittest.TestCase):
    def test_save_and_load_restores_hotbar(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            world = World()
            player = Player()
            player.inventory.add(BlockType.WOOD)
            player.inventory.add(ItemType.APPLE)

            hotbar = [BlockType.WOOD, ItemType.APPLE, None, None, None]
            save_manager = SaveManager(tmpdir, "slot-test")
            save_manager.save(world, player, seed=123, hotbar=hotbar, hotbar_index=1)

            loaded_world = World()
            loaded_player = Player()
            loaded_seed, loaded_hotbar, loaded_hotbar_index = save_manager.load(loaded_world, loaded_player)

            self.assertEqual(loaded_seed, 123)
            self.assertEqual(loaded_hotbar, hotbar)
            self.assertEqual(loaded_hotbar_index, 1)

    def test_load_without_hotbar_fields_defaults_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            world = World()
            player = Player()
            save_manager = SaveManager(tmpdir, "legacy-test")
            save_manager.save_path.mkdir(parents=True, exist_ok=True)
            save_manager._write_meta(321)
            save_manager._write_world(world)
            with open(save_manager.save_path / "player.json", "w") as f:
                f.write('{"x": 0, "y": 0, "health": 10, "breath": 10, "facing_right": true, "inventory": {}, "armor": {}}')

            loaded_player = Player()
            loaded_seed, loaded_hotbar, loaded_hotbar_index = save_manager.load(World(), loaded_player)

            self.assertEqual(loaded_seed, 321)
            self.assertEqual(loaded_hotbar, [])
            self.assertEqual(loaded_hotbar_index, 0)
