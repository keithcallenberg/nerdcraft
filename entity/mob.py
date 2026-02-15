"""Mob entities with simple AI."""

from __future__ import annotations

from world.block import BlockType


class Mob:
    """A mob entity with physics-compatible attributes and simple AI."""

    def __init__(self, x: int, y: int, mob_type: str = "cow",
                 char: str = "C", color: str = "white", health: int = 10):
        self.x = x
        self.y = y
        self.mob_type = mob_type
        self.char = char
        self.color = color
        self.health = health

        # Physics state (duck-typed with Player for PhysicsEngine)
        self.on_ground = False
        self.jump_remaining = 0
        self.fall_distance = 0
        self.facing_right = True

        # AI state
        self._ai_timer = 0.0
        self._ai_state = "idle"
        self._walk_dir = 0  # -1 left, 1 right

    @property
    def is_alive(self) -> bool:
        return self.health > 0

    @property
    def drops(self) -> list[BlockType]:
        if self.mob_type == "cow":
            return [BlockType.LEATHER]
        return []

    def update_ai(self, world, dt: float) -> int:
        """Update AI state. Returns desired dx movement (0, -1, or 1)."""
        self._ai_timer -= dt
        if self._ai_timer <= 0:
            # Pick a new action every 1-2 seconds
            # Use a simple hash of position + health as pseudo-random
            h = (self.x * 31 + self.y * 17 + int(self._ai_timer * 100)) & 255
            self._ai_timer = 1.0 + (h % 100) / 100.0

            if h % 3 == 0:
                self._ai_state = "idle"
                self._walk_dir = 0
            else:
                self._ai_state = "walk"
                self._walk_dir = 1 if h % 2 == 0 else -1
                self.facing_right = self._walk_dir > 0

        if self._ai_state == "walk":
            return self._walk_dir
        return 0
