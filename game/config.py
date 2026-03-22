"""Game configuration constants loaded from JSON."""

from __future__ import annotations
from config import GameConfig

# Get the singleton config instance
_cfg = GameConfig.get()

# Game loop
TICK_RATE = _cfg.tick_rate
TICK_DURATION = _cfg.tick_duration

# World dimensions
CHUNK_SIZE = _cfg.chunk_size
WORLD_WIDTH_CHUNKS = _cfg.world_width_chunks
WORLD_HEIGHT_CHUNKS = _cfg.world_height_chunks
WORLD_WIDTH = _cfg.world_width
WORLD_HEIGHT = _cfg.world_height

# Terrain generation
SEA_LEVEL = _cfg.sea_level
DIRT_DEPTH = _cfg.dirt_depth
STONE_DEPTH = _cfg.stone_depth

# Physics
GRAVITY_INTERVAL = _cfg.gravity_interval
JUMP_HEIGHT = _cfg.jump_height
SAFE_FALL_DISTANCE = _cfg.safe_fall_distance
FALL_DAMAGE_PER_BLOCK = _cfg.fall_damage_per_block
AUTO_JUMP = _cfg.auto_jump

# Player
PLAYER_CHAR = _cfg.player_char

# Save
AUTO_SAVE_TICKS = _cfg.save.auto_save_ticks
SAVE_DIR = _cfg.save.save_dir
