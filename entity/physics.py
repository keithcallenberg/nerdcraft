"""Physics engine with discrete grid-based gravity and jumping."""

from __future__ import annotations
from entity.player import Player
from world.world import World


class PhysicsEngine:
    """Handles discrete grid-based physics."""

    def __init__(self, world: World, gravity_interval: float, jump_height: int):
        """Initialize physics with world reference and tuning parameters.

        gravity_interval: seconds between each 1-block gravity/jump step.
        jump_height: number of blocks a jump rises.
        """
        self.world = world
        self.gravity_interval = gravity_interval
        self.jump_height = jump_height
        self._gravity_timer = 0.0

    def update(self, player: Player, dt: float) -> None:
        """Accumulate time and perform discrete gravity steps."""
        self._gravity_timer += dt

        while self._gravity_timer >= self.gravity_interval:
            self._gravity_timer -= self.gravity_interval
            self._gravity_step(player)

    def _gravity_step(self, player: Player) -> None:
        """Perform one discrete gravity or jump step."""
        if player.jump_remaining > 0:
            # Rising — try to move up
            if not self.world.is_solid(player.x, player.y + 1):
                player.y += 1
                player.jump_remaining -= 1
                player.on_ground = False
            else:
                # Hit ceiling, cancel remaining jump
                player.jump_remaining = 0
        else:
            # Falling — try to move down
            if not self.world.is_solid(player.x, player.y - 1):
                player.y -= 1
                player.on_ground = False
            else:
                player.on_ground = True

    def try_move(self, player: Player, dx: int, dy: int) -> bool:
        """Try to move player by (dx, dy). Returns True if successful."""
        target_x = player.x + dx
        target_y = player.y + dy
        if not self.world.is_solid(target_x, target_y):
            player.x = target_x
            player.y = target_y
            return True
        return False
