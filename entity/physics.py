"""Physics engine with discrete grid-based gravity and jumping."""

from __future__ import annotations
from world.world import World


class PhysicsEngine:
    """Handles discrete grid-based physics."""

    def __init__(self, world: World, gravity_interval: float, jump_height: int,
                 safe_fall_distance: int = 6, fall_damage_per_block: int = 5):
        """Initialize physics with world reference and tuning parameters."""
        self.world = world
        self.gravity_interval = gravity_interval
        self.jump_height = jump_height
        self.safe_fall_distance = safe_fall_distance
        self.fall_damage_per_block = fall_damage_per_block
        self._gravity_timers: dict[int, float] = {}

    def update(self, entity, dt: float) -> None:
        """Accumulate time and perform discrete gravity steps."""
        eid = id(entity)
        timer = self._gravity_timers.get(eid, 0.0) + dt

        while timer >= self.gravity_interval:
            timer -= self.gravity_interval
            self._gravity_step(entity)

        self._gravity_timers[eid] = timer

    def _gravity_step(self, entity) -> None:
        """Perform one discrete gravity or jump step."""
        if entity.jump_remaining > 0:
            # Rising — try to move up
            if not self.world.is_solid(entity.x, entity.y + 1):
                entity.y += 1
                entity.jump_remaining -= 1
                entity.on_ground = False
            else:
                # Hit ceiling, cancel remaining jump
                entity.jump_remaining = 0
            # Reset fall distance while rising
            entity.fall_distance = 0
        else:
            # Falling — try to move down
            if not self.world.is_solid(entity.x, entity.y - 1):
                entity.y -= 1
                entity.fall_distance += 1
                entity.on_ground = False
            else:
                # Landed — apply fall damage if needed
                if entity.fall_distance > self.safe_fall_distance:
                    excess = entity.fall_distance - self.safe_fall_distance
                    damage = excess * self.fall_damage_per_block
                    entity.health = max(0, entity.health - damage)
                entity.fall_distance = 0
                entity.on_ground = True

    def try_move(self, entity, dx: int, dy: int) -> bool:
        """Try to move entity by (dx, dy). Returns True if successful."""
        target_x = entity.x + dx
        target_y = entity.y + dy
        if not self.world.is_solid(target_x, target_y):
            entity.x = target_x
            entity.y = target_y
            return True
        return False
