"""Block types and their properties, loaded from JSON configuration."""

from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, Optional


class BlockType(Enum):
    """All block types in the game.

    These are dynamically mapped to JSON config block names.
    The enum names should match the JSON keys (uppercase vs lowercase).
    """
    AIR = auto()
    GRASS = auto()
    DIRT = auto()
    STONE = auto()
    COAL_ORE = auto()
    IRON_ORE = auto()
    GOLD_ORE = auto()
    DIAMOND_ORE = auto()
    BEDROCK = auto()
    TRUNK = auto()
    LEAVES = auto()
    WATER = auto()
    CONCRETE = auto()

@dataclass(frozen=True)
class BlockProperties:
    """Properties for a block type."""
    char: str  # ASCII character to render
    solid: bool = True  # Can be collided with
    breakable: bool = True  # Can be mined
    color_pair: int = 0  # Curses color pair index


# Block properties registry - will be populated from JSON
_block_properties: Dict[BlockType, BlockProperties] = {}
_initialized = False


def _get_json_name(block_type: BlockType) -> str:
    """Convert BlockType enum to JSON config name."""
    return block_type.name.lower()


def _init_from_config() -> None:
    """Initialize block properties from JSON configuration."""
    global _block_properties, _initialized

    if _initialized:
        return

    from config import GameConfig
    cfg = GameConfig.get()

    for block_type in BlockType:
        json_name = _get_json_name(block_type)
        block_cfg = cfg.get_block(json_name)

        if block_cfg:
            color_pair = cfg.get_block_color_pair(json_name)
            _block_properties[block_type] = BlockProperties(
                char=block_cfg.char,
                solid=block_cfg.solid,
                breakable=block_cfg.breakable,
                color_pair=color_pair
            )
        else:
            # Fallback for blocks not in config
            _block_properties[block_type] = BlockProperties(
                char='?',
                solid=True,
                breakable=True,
                color_pair=0
            )

    _initialized = True


def get_properties(block_type: BlockType) -> BlockProperties:
    """Get properties for a block type."""
    _init_from_config()
    return _block_properties[block_type]


def is_solid(block_type: BlockType) -> bool:
    """Check if a block type is solid (collidable)."""
    _init_from_config()
    return _block_properties[block_type].solid


def reload_config() -> None:
    """Reload block properties from JSON configuration."""
    global _initialized
    _initialized = False
    from config import GameConfig
    GameConfig.reload()
    _init_from_config()
