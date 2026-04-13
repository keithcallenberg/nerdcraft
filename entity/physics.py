"""Physics engine with discrete grid-based gravity and jumping."""

from __future__ import annotations

from world.block import BlockType
from world.world import World


class PhysicsEngine:
    """Handles discrete grid-based physics."""

    def __init__(
        self,
        world: World,
        gravity_interval: float,
        jump_height: int,
        safe_fall_distance: int = 6,
        fall_damage_per_block: int = 5,
        auto_jump: bool = True,
        in_water_gravity_multiplier: float = 2.2,
    ):
        """Initialize physics with world reference and tuning parameters."""
        self.world = world
        self.gravity_interval = gravity_interval
        self.jump_height = jump_height
        self.safe_fall_distance = safe_fall_distance
        self.fall_damage_per_block = fall_damage_per_block
        self.auto_jump = auto_jump
        self.in_water_gravity_multiplier = max(1.0, float(in_water_gravity_multiplier))
        self._gravity_timers: dict[int, float] = {}

    def update(self, entity, dt: float) -> None:
        """Accumulate time and perform discrete gravity steps."""
        eid = id(entity)
        timer = self._gravity_timers.get(eid, 0.0) + dt

        step_interval = self.gravity_interval
        if self.world.get_block(entity.x, entity.y) == BlockType.WATER:
            step_interval = self.gravity_interval * self.in_water_gravity_multiplier

        while timer >= step_interval:
            timer -= step_interval
            self._gravity_step(entity)

        self._gravity_timers[eid] = timer

    def _gravity_step(self, entity) -> None:
        """Perform one discrete gravity or jump step."""
        in_water = self.world.get_block(entity.x, entity.y) == BlockType.WATER

        if entity.jump_remaining > 0:
            # Rising — try to move up
            if not self.world.is_solid(entity.x, entity.y + 1, entity=entity):
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
            if not self.world.is_solid(entity.x, entity.y - 1, entity=entity):
                entity.y -= 1
                entity.fall_distance += 1
                entity.on_ground = False
            else:
                # Landed — apply fall damage if needed (not in water)
                if (not in_water) and entity.fall_distance > self.safe_fall_distance:
                    excess = entity.fall_distance - self.safe_fall_distance
                    damage = excess * self.fall_damage_per_block
                    entity.health = max(0, entity.health - damage)
                entity.fall_distance = 0
                entity.on_ground = True

    def try_move(self, entity, dx: int, dy: int) -> bool:
        """Try to move entity by (dx, dy). Returns True if successful."""
        target_x = entity.x + dx
        target_y = entity.y + dy
        if not self.world.is_solid(target_x, target_y, entity=entity):
            entity.x = target_x
            entity.y = target_y
            return True

        # Auto-jump assist for horizontal movement into 1-block obstacles.
        if (
            self.auto_jump
            and dy == 0
            and dx != 0
            and getattr(entity, 'on_ground', False)
            and getattr(entity, 'jump_remaining', 0) <= 0
        ):
            # Need headroom at current x and open step-up target.
            can_raise_here = not self.world.is_solid(entity.x, entity.y + 1, entity=entity)
            can_step_up = not self.world.is_solid(target_x, entity.y + 1, entity=entity)
            if can_raise_here and can_step_up:
                entity.x = target_x
                entity.y = entity.y + 1
                entity.on_ground = False
                entity.jump_remaining = max(0, self.jump_height - 1)
                return True

        return False
