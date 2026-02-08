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
GRAVITY = _cfg.gravity
MAX_FALL_SPEED = _cfg.max_fall_speed

# Player
PLAYER_SPEED = _cfg.player_speed
JUMP_VELOCITY = _cfg.jump_velocity
PLAYER_WIDTH = _cfg.player_width
PLAYER_HEIGHT = _cfg.player_height
PLAYER_CHAR = _cfg.player_char
