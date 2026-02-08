"""Physics engine with gravity and AABB collision."""

from __future__ import annotations
import math
from game.config import GRAVITY, MAX_FALL_SPEED, TICK_DURATION
from entity.player import Player
from world.world import World


class PhysicsEngine:
    """Handles physics simulation for entities."""

    def __init__(self, world: World):
        """Initialize physics engine with world reference."""
        self.world = world

    def update(self, player: Player, dt: float) -> None:
        """Update player physics for one timestep."""
        # Apply gravity
        player.velocity.y -= GRAVITY * dt

        # Clamp fall speed
        if player.velocity.y < -MAX_FALL_SPEED:
            player.velocity.y = -MAX_FALL_SPEED

        # Move and resolve collisions separately for each axis
        self._move_x(player, player.velocity.x * dt)
        self._move_y(player, player.velocity.y * dt)

    def _move_x(self, player: Player, dx: float) -> None:
        """Move player horizontally with collision detection."""
        if dx == 0:
            return

        new_x = player.x + dx
        player.x = new_x

        # Check for collisions
        left, bottom, right, top = player.get_aabb()

        # Get blocks player overlaps with
        min_bx = int(math.floor(left))
        max_bx = int(math.floor(right))
        min_by = int(math.floor(bottom))
        max_by = int(math.floor(top - 0.001))  # Slight offset to avoid ceiling issues

        for bx in range(min_bx, max_bx + 1):
            for by in range(min_by, max_by + 1):
                if self.world.is_solid(bx, by):
                    # Resolve collision
                    if dx > 0:
                        # Moving right, push left
                        player.x = bx - player.width / 2 - 0.001
                    else:
                        # Moving left, push right
                        player.x = bx + 1 + player.width / 2 + 0.001
                    player.velocity.x = 0
                    return

    def _move_y(self, player: Player, dy: float) -> None:
        """Move player vertically with collision detection."""
        if dy == 0:
            return

        new_y = player.y + dy
        player.y = new_y
        player.on_ground = False

        # Check for collisions
        left, bottom, right, top = player.get_aabb()

        # Get blocks player overlaps with
        min_bx = int(math.floor(left + 0.001))
        max_bx = int(math.floor(right - 0.001))
        min_by = int(math.floor(bottom))
        max_by = int(math.floor(top - 0.001))

        for bx in range(min_bx, max_bx + 1):
            for by in range(min_by, max_by + 1):
                if self.world.is_solid(bx, by):
                    # Resolve collision
                    if dy < 0:
                        # Falling, land on block
                        player.y = by + 1
                        player.velocity.y = 0
                        player.on_ground = True
                    else:
                        # Jumping, hit ceiling
                        player.y = by - player.height - 0.001
                        player.velocity.y = 0
                    return

    def check_collision(self, player: Player) -> bool:
        """Check if player is currently colliding with any solid block."""
        left, bottom, right, top = player.get_aabb()

        min_bx = int(math.floor(left + 0.001))
        max_bx = int(math.floor(right - 0.001))
        min_by = int(math.floor(bottom + 0.001))
        max_by = int(math.floor(top - 0.001))

        for bx in range(min_bx, max_bx + 1):
            for by in range(min_by, max_by + 1):
                if self.world.is_solid(bx, by):
                    return True
        return False
