"""Configuration loading and management."""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass


# Find the config directory relative to this file
CONFIG_DIR = Path(__file__).parent
# Project root (one level up from config/)
PROJECT_ROOT = CONFIG_DIR.parent


def _load_json(filename: str) -> Dict[str, Any]:
    """Load a JSON file from the config directory."""
    filepath = CONFIG_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Config file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)


@dataclass
class BlockConfig:
    """Configuration for a single block type."""
    name: str
    char: str
    solid: bool
    breakable: bool
    color: str


@dataclass
class ColorConfig:
    """Configuration for a color pair."""
    name: str
    pair_id: int
    foreground: str
    background: str
    bold: bool = False


@dataclass
class SaveConfig:
    """Configuration for the save/load system."""
    auto_save_ticks: int
    save_dir: Path


class GameConfig:
    """Centralized game configuration loaded from JSON files."""

    _instance: Optional[GameConfig] = None

    def __init__(self):
        """Load all configuration files."""
        self._load_game_config()
        self._load_blocks_config()
        self._load_colors_config()

    @classmethod
    def get(cls) -> GameConfig:
        """Get the singleton config instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reload(cls) -> GameConfig:
        """Force reload of configuration."""
        cls._instance = cls()
        return cls._instance

    def _load_game_config(self) -> None:
        """Load game.json configuration."""
        data = _load_json('game.json')

        # Game loop
        game_loop = data.get('game_loop', {})
        self.tick_rate = game_loop.get('tick_rate', 60)
        self.tick_duration = 1.0 / self.tick_rate

        # World
        world = data.get('world', {})
        self.chunk_size = world.get('chunk_size', 16)
        self.world_width_chunks = world.get('width_chunks', 64)
        self.world_height_chunks = world.get('height_chunks', 16)
        self.world_width = self.world_width_chunks * self.chunk_size
        self.world_height = self.world_height_chunks * self.chunk_size

        # Terrain
        terrain = data.get('terrain', {})
        sea_level_ratio = terrain.get('sea_level_ratio', 0.5)
        self.sea_level = int(self.world_height * sea_level_ratio)
        self.dirt_depth = terrain.get('dirt_depth', 4)
        self.stone_depth = terrain.get('stone_depth', 20)

        # Physics
        physics = data.get('physics', {})
        self.gravity_interval = physics.get('gravity_interval', 0.1)
        self.jump_height = physics.get('jump_height', 5)
        self.safe_fall_distance = physics.get('safe_fall_distance', 6)
        self.fall_damage_per_block = physics.get('fall_damage_per_block', 5)

        # Player
        player = data.get('player', {})
        self.player_char = player.get('char', '@')

        # Save
        save = data.get('save', {})
        save_dir_str = save.get('save_dir', 'saves')
        # Resolve relative to project root
        save_dir = Path(save_dir_str)
        if not save_dir.is_absolute():
            save_dir = PROJECT_ROOT / save_dir
        self.save = SaveConfig(
            auto_save_ticks=save.get('auto_save_ticks', 3600),
            save_dir=save_dir,
        )

    def _load_blocks_config(self) -> None:
        """Load blocks.json configuration."""
        data = _load_json('blocks.json')
        self.blocks: Dict[str, BlockConfig] = {}

        for name, props in data.get('blocks', {}).items():
            self.blocks[name] = BlockConfig(
                name=name,
                char=props.get('char', '?'),
                solid=props.get('solid', True),
                breakable=props.get('breakable', True),
                color=props.get('color', 'default')
            )

    def _load_colors_config(self) -> None:
        """Load colors.json configuration."""
        data = _load_json('colors.json')
        self.colors: Dict[str, ColorConfig] = {}

        for name, props in data.get('colors', {}).items():
            self.colors[name] = ColorConfig(
                name=name,
                pair_id=props.get('pair_id', 0),
                foreground=props.get('foreground', 'default'),
                background=props.get('background', 'default'),
                bold=props.get('bold', False)
            )

    def get_block(self, name: str) -> BlockConfig:
        """Get block configuration by name."""
        return self.blocks.get(name, self.blocks.get('air'))

    def get_color(self, name: str) -> ColorConfig:
        """Get color configuration by name."""
        return self.colors.get(name, self.colors.get('default'))

    def get_block_color_pair(self, block_name: str) -> int:
        """Get the curses color pair ID for a block."""
        block = self.get_block(block_name)
        color = self.get_color(block.color)
        return color.pair_id if color else 0
