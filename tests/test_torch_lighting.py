"""Tests for torch lighting config/plumbing."""

from __future__ import annotations

import unittest

from world.block import BlockType, get_properties


class TorchLightingConfigTests(unittest.TestCase):
    def test_torch_has_positive_light_radius(self) -> None:
        torch_props = get_properties(BlockType.TORCH)
        self.assertGreater(torch_props.light_radius, 0)


if __name__ == "__main__":
    unittest.main()
