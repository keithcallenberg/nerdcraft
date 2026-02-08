"""Block types and their properties."""

from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict


class BlockType(Enum):
    """All block types in the game."""
    AIR = auto()
    GRASS = auto()
    DIRT = auto()
    STONE = auto()
    COAL_ORE = auto()
    IRON_ORE = auto()
    GOLD_ORE = auto()
    DIAMOND_ORE = auto()
    BEDROCK = auto()
    WOOD = auto()
    LEAVES = auto()


@dataclass(frozen=True)
class BlockProperties:
    """Properties for a block type."""
    char: str  # ASCII character to render
    solid: bool = True  # Can be collided with
    breakable: bool = True  # Can be mined
    color_pair: int = 0  # Curses color pair index


# Block properties registry
BLOCK_PROPERTIES: dict[BlockType, BlockProperties] = {
    BlockType.AIR: BlockProperties(char=" ", solid=False, breakable=False, color_pair=0),
    BlockType.GRASS: BlockProperties(char="#", solid=True, breakable=True, color_pair=1),
    BlockType.DIRT: BlockProperties(char="#", solid=True, breakable=True, color_pair=2),
    BlockType.STONE: BlockProperties(char="#", solid=True, breakable=True, color_pair=3),
    BlockType.COAL_ORE: BlockProperties(char="o", solid=True, breakable=True, color_pair=4),
    BlockType.IRON_ORE: BlockProperties(char="o", solid=True, breakable=True, color_pair=5),
    BlockType.GOLD_ORE: BlockProperties(char="o", solid=True, breakable=True, color_pair=6),
    BlockType.DIAMOND_ORE: BlockProperties(char="*", solid=True, breakable=True, color_pair=7),
    BlockType.BEDROCK: BlockProperties(char="X", solid=True, breakable=False, color_pair=3),
    BlockType.WOOD: BlockProperties(char="|", solid=True, breakable=True, color_pair=2),
    BlockType.LEAVES: BlockProperties(char="*", solid=False, breakable=True, color_pair=1),
}


def get_properties(block_type: BlockType) -> BlockProperties:
    """Get properties for a block type."""
    return BLOCK_PROPERTIES[block_type]


def is_solid(block_type: BlockType) -> bool:
    """Check if a block type is solid (collidable)."""
    return BLOCK_PROPERTIES[block_type].solid
