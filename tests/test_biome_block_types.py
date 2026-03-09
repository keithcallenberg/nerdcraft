import unittest

from world.block import BlockType, get_properties, reload_config
from world.generator import WorldGenerator


class TestBiomeBlockTypes(unittest.TestCase):
    def setUp(self):
        reload_config()

    def test_new_biome_blocks_have_properties(self):
        for block_type in (BlockType.SAND, BlockType.CACTUS, BlockType.SNOW, BlockType.ICE):
            props = get_properties(block_type)
            self.assertNotEqual(props.char, "?")

    def test_generator_maps_biome_blocks_to_enum(self):
        gen = WorldGenerator(seed=123)
        self.assertEqual(gen._to_block_type("sand", BlockType.GRASS), BlockType.SAND)
        self.assertEqual(gen._to_block_type("snow", BlockType.GRASS), BlockType.SNOW)


if __name__ == "__main__":
    unittest.main()
