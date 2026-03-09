import unittest

from entity.crafting import RecipeEngine
from entity.inventory import Inventory
from world.block import BlockType


class TestCraftingProgression(unittest.TestCase):
    def test_chop_wood_to_workbench_flow(self):
        engine = RecipeEngine()
        inventory = Inventory()

        # Simulate chopping one wood block.
        inventory.add(BlockType.WOOD)

        # Can craft planks from wood.
        available_ids = {recipe.recipe_id for recipe in engine.available_recipes(inventory)}
        self.assertIn("wood_to_planks", available_ids)

        crafted_planks = engine.craft(inventory, "wood_to_planks")
        self.assertTrue(crafted_planks)
        self.assertEqual(inventory.count(BlockType.WOOD), 0)
        self.assertEqual(inventory.count(BlockType.WOOD_PLANK), 4)

        # Can craft workbench from planks.
        available_ids = {recipe.recipe_id for recipe in engine.available_recipes(inventory)}
        self.assertIn("planks_to_workbench", available_ids)

        crafted_workbench = engine.craft(inventory, "planks_to_workbench")
        self.assertTrue(crafted_workbench)
        self.assertEqual(inventory.count(BlockType.WOOD_PLANK), 0)
        self.assertEqual(inventory.count(BlockType.WORKBENCH), 1)


if __name__ == "__main__":
    unittest.main()
