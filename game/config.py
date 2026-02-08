"""Game configuration constants."""

# Game loop
TICK_RATE = 60  # Updates per second
TICK_DURATION = 1.0 / TICK_RATE  # Seconds per tick

# World dimensions
CHUNK_SIZE = 16  # Blocks per chunk (width and height)
WORLD_WIDTH_CHUNKS = 64  # Total chunks horizontally
WORLD_HEIGHT_CHUNKS = 16  # Total chunks vertically
WORLD_WIDTH = WORLD_WIDTH_CHUNKS * CHUNK_SIZE  # Total blocks horizontally
WORLD_HEIGHT = WORLD_HEIGHT_CHUNKS * CHUNK_SIZE  # Total blocks vertically

# Terrain generation
SEA_LEVEL = WORLD_HEIGHT // 2  # Surface level
DIRT_DEPTH = 4  # Dirt blocks below grass
STONE_DEPTH = 20  # Stone starts this many blocks below surface

# Physics
GRAVITY = 30.0  # Blocks per second squared (downward)
PLAYER_SPEED = 8.0  # Blocks per second
JUMP_VELOCITY = 12.0  # Initial upward velocity when jumping
MAX_FALL_SPEED = 25.0  # Terminal velocity

# Player dimensions (in blocks)
PLAYER_WIDTH = 0.6
PLAYER_HEIGHT = 1.8

# Rendering
PLAYER_CHAR = "@"
