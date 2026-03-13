"""Configuration loading and management."""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass
from collections.abc import Mapping


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
    light_radius: int = 0


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


@dataclass
class SoundEventConfig:
    """Configuration for a single sound event cue."""
    enabled: bool = True
    cooldown: float = 0.1
    beep_count: int = 1


@dataclass
class CombatConfig:
    max_health: int = 100
    fist_attack_damage: int = 5
    tool_attack_damage: int = 5
    consumable_use_clamps_to_max_health: bool = True
    need_tool_template: str = "Need {tool} for {block}"


@dataclass
class EngineConfig:
    frame_cap_seconds: float = 0.25
    sleep_seconds: float = 0.001
    save_flash_duration: float = 2.0
    death_screen_duration: float = 2.0
    status_flash_duration: float = 1.2
    night_spawn_interval_ticks: int = 900
    night_spawn_cap: int = 18
    night_spawn_min_player_distance: int = 12


class GameConfig:
    """Centralized game configuration loaded from JSON files."""

    _instance: Optional[GameConfig] = None

    def __init__(self):
        """Load all configuration files."""
        self._load_game_config()
        self._load_blocks_config()
        self._load_colors_config()
        self._load_sounds_config()
        self._load_input_config()
        self._load_combat_config()
        self._load_mining_config()
        self._load_ui_config()
        self._load_engine_config()

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
        self.day_length_ticks = game_loop.get('day_length_ticks', 36000)

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
                color=props.get('color', 'default'),
                light_radius=props.get('light_radius', 0),
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

    def _load_sounds_config(self) -> None:
        """Load sounds.json configuration."""
        data = _load_json('sounds.json')
        self.sounds: Dict[str, SoundEventConfig] = {}

        for name, props in data.get('events', {}).items():
            if not isinstance(props, Mapping):
                continue
            self.sounds[name] = SoundEventConfig(
                enabled=bool(props.get('enabled', True)),
                cooldown=float(props.get('cooldown', 0.1)),
                beep_count=max(1, int(props.get('beep_count', 1))),
            )

    def get_block(self, name: str) -> BlockConfig:
        """Get block configuration by name."""
        return self.blocks.get(name, self.blocks.get('air'))

    def get_color(self, name: str) -> ColorConfig:
        """Get color configuration by name."""
        return self.colors.get(name, self.colors.get('default'))

    def _load_input_config(self) -> None:
        """Load input.json configuration."""
        data = _load_json('input.json')
        self.input_bindings: Dict[str, list[str]] = {
            name: [str(k) for k in keys]
            for name, keys in data.get('bindings', {}).items()
            if isinstance(keys, list)
        }

    def _load_combat_config(self) -> None:
        """Load combat.json configuration."""
        data = _load_json('combat.json')
        player = data.get('player', {})
        status = data.get('status_messages', {})
        self.combat = CombatConfig(
            max_health=int(player.get('max_health', 100)),
            fist_attack_damage=int(player.get('fist_attack_damage', 5)),
            tool_attack_damage=int(player.get('tool_attack_damage', 5)),
            consumable_use_clamps_to_max_health=bool(
                player.get('consumable_use_clamps_to_max_health', True)
            ),
            need_tool_template=str(
                status.get('need_tool_template', 'Need {tool} for {block}')
            ),
        )

    def _load_mining_config(self) -> None:
        """Load mining.json configuration."""
        data = _load_json('mining.json')
        self.mining_required_tiers: Dict[str, int] = {
            str(name): int(tier)
            for name, tier in data.get('required_tiers', {}).items()
        }
        self.mining_tier_names: Dict[int, str] = {
            int(tier): str(name)
            for tier, name in data.get('tier_names', {}).items()
        }
        drops = data.get('drops', {})
        leaves = drops.get('leaves', {}) if isinstance(drops, Mapping) else {}
        self.leaf_apple_chance = float(leaves.get('apple_chance', 0.12))

    def _load_ui_config(self) -> None:
        """Load ui.json configuration."""
        data = _load_json('ui.json')
        self.ui: Dict[str, Any] = data

    def _load_engine_config(self) -> None:
        """Load engine.json configuration."""
        data = _load_json('engine.json')
        loop = data.get('loop', {})
        timers = data.get('timers', {})
        night = data.get('night_spawns', {})
        self.engine = EngineConfig(
            frame_cap_seconds=float(loop.get('frame_cap_seconds', 0.25)),
            sleep_seconds=float(loop.get('sleep_seconds', 0.001)),
            save_flash_duration=float(timers.get('save_flash_duration', 2.0)),
            death_screen_duration=float(timers.get('death_screen_duration', 2.0)),
            status_flash_duration=float(timers.get('status_flash_duration', 1.2)),
            night_spawn_interval_ticks=int(night.get('interval_ticks', 900)),
            night_spawn_cap=int(night.get('mob_cap', 18)),
            night_spawn_min_player_distance=int(night.get('min_player_distance', 12)),
        )

    def get_ui_text(self, section: str, key: str, default: str = "") -> str:
        section_obj = self.ui.get(section, {}) if isinstance(self.ui, dict) else {}
        if isinstance(section_obj, dict):
            return str(section_obj.get(key, default))
        return default

    def get_ui_int(self, section: str, key: str, default: int) -> int:
        section_obj = self.ui.get(section, {}) if isinstance(self.ui, dict) else {}
        if isinstance(section_obj, dict):
            return int(section_obj.get(key, default))
        return default

    def get_block_color_pair(self, block_name: str) -> int:
        """Get the curses color pair ID for a block."""
        block = self.get_block(block_name)
        color = self.get_color(block.color)
        return color.pair_id if color else 0
