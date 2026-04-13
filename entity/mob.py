"""Mob entities with data-driven AI loaded from config/mobs.json."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from entity.item import ItemType
from entity.mob_registry import MobRegistry, MobDef
from world.block import BlockType

if TYPE_CHECKING:
    from world.world import World

# AI states
_IDLE   = "idle"
_WALK   = "walk"
_CHASE  = "chase"
_ATTACK = "attack"


class Mob:
    """A mob entity whose behaviour is defined by config/mobs.json.

    All attributes that PhysicsEngine needs (x, y, on_ground,
    jump_remaining, fall_distance, health) are present so that the
    physics engine can treat mobs and the player identically.
    """

    def __init__(self, x: int, y: int, mob_id: str = "cow"):
        self.x = x
        self.y = y
        self.mob_id = mob_id

        # Pull definition from registry
        reg = MobRegistry.get()
        defn = reg.get_def(mob_id)
        if defn is None:
            raise ValueError(f"Unknown mob type: {mob_id!r}")
        self._defn: MobDef = defn

        # Stats (mutable copies from definition)
        self.health: int = defn.health
        self.char: str = defn.char
        self.color: str = defn.color
        self.mob_type: str = mob_id   # legacy alias used by renderer

        # Physics state (duck-typed with Player for PhysicsEngine)
        self.on_ground: bool = False
        self.jump_remaining: int = 0
        self.fall_distance: int = 0
        self.facing_right: bool = True

        # AI state
        self._state: str = _IDLE
        self._move_timer: float = 0.0
        self._attack_timer: float = 0.0
        self._walk_dir: int = 0          # -1 left, +1 right
        self._wander_steps_remaining: int = 0
        # Small per-mob RNG so behaviour varies between individuals
        self._rng = random.Random(id(self))

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def is_alive(self) -> bool:
        return self.health > 0

    @property
    def hostile(self) -> bool:
        return self._defn.hostile

    @property
    def name(self) -> str:
        return self._defn.name

    @property
    def drops(self) -> list[BlockType | ItemType]:
        """Resolve drop list using per-drop chance rolls."""
        result: list[BlockType | ItemType] = []
        _name_to_block = {b.name: b for b in BlockType}
        _name_to_item = {i.name: i for i in ItemType}
        for drop in self._defn.drops:
            if self._rng.random() <= drop.chance:
                inv_item = _name_to_item.get(drop.item) or _name_to_block.get(drop.item)
                if inv_item is not None:
                    for _ in range(drop.count):
                        result.append(inv_item)
        return result

    # ------------------------------------------------------------------
    # AI update — called once per game tick
    # ------------------------------------------------------------------

    def update_ai(self, world: "World", dt: float,
                  player_x: int | None = None,
                  player_y: int | None = None) -> int:
        """Update AI state machine.  Returns desired dx: -1, 0, or +1.

        Parameters
        ----------
        world:
            The game world (used for obstacle checks).
        dt:
            Elapsed time in seconds since last call.
        player_x, player_y:
            Player position, required for hostile mob logic.
            If None the mob acts as passive regardless of config.
        """
        defn = self._defn

        # --- Hostile logic: override state based on player proximity ---
        if defn.hostile and player_x is not None:
            dist = abs(self.x - player_x)
            adjacent = (dist <= 1 and abs(self.y - player_y) <= 1)

            if adjacent:
                self._state = _ATTACK
            elif dist <= defn.detection_range:
                self._state = _CHASE
            elif self._state in (_CHASE, _ATTACK):
                # Lost sight of player — go back to wandering
                self._state = _IDLE
                self._move_timer = 0.0

        # --- Attack state ---
        if self._state == _ATTACK:
            self._attack_timer -= dt
            # No horizontal movement while attacking
            return 0

        # --- Chase state ---
        if self._state == _CHASE and player_x is not None:
            self._move_timer -= dt
            if self._move_timer <= 0:
                self._move_timer = defn.move_interval
                dx = 1 if player_x > self.x else -1
                self.facing_right = dx > 0
                return dx
            return 0

        # --- Passive wander (idle / walk) ---
        self._move_timer -= dt
        if self._move_timer <= 0:
            if self._state == _WALK and self._wander_steps_remaining > 0:
                self._wander_steps_remaining -= 1
                self._move_timer = defn.idle_move_interval
                return self._walk_dir

            # Pick next action
            roll = self._rng.random()
            if roll < 0.55:
                self._state = _IDLE
                self._walk_dir = 0
                self._wander_steps_remaining = 0
                self._move_timer = self._rng.uniform(1.4, 3.2)
            else:
                self._state = _WALK
                if self._walk_dir == 0 or self._rng.random() < 0.15:
                    self._walk_dir = self._rng.choice([-1, 1])
                self.facing_right = self._walk_dir > 0
                self._wander_steps_remaining = self._rng.randint(1, 3)
                self._move_timer = defn.idle_move_interval
                return self._walk_dir

        if self._state == _WALK and self._wander_steps_remaining > 0:
            return 0
        return 0

    def get_attack_damage(self) -> int:
        """Return damage this mob deals when attacking."""
        return self._defn.attack_damage

    def get_move_speed(self) -> int:
        """Return blocks moved per movement action."""
        return max(1, self._defn.move_speed)

    def can_attack_now(self) -> bool:
        """True when the attack cooldown has expired."""
        return self._attack_timer <= 0

    def reset_attack_timer(self) -> None:
        """Reset cooldown after performing an attack."""
        self._attack_timer = self._defn.attack_interval
