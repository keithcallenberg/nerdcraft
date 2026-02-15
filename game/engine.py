"""Main game engine with fixed-timestep game loop."""

from __future__ import annotations
import time
from game.config import (
    TICK_DURATION, GRAVITY_INTERVAL, JUMP_HEIGHT,
    SAFE_FALL_DISTANCE, FALL_DAMAGE_PER_BLOCK,
)
from world.world import World
from world.block import BlockType, get_properties
from world.generator import WorldGenerator
from entity.player import Player
from entity.physics import PhysicsEngine
from render.renderer import Renderer
from input.handler import InputHandler, Action


class GameEngine:
    """Main game engine orchestrating all systems."""

    HOTBAR_SIZE = 5

    _HOTBAR_SELECT = {
        Action.HOTBAR_1: 0,
        Action.HOTBAR_2: 1,
        Action.HOTBAR_3: 2,
        Action.HOTBAR_4: 3,
        Action.HOTBAR_5: 4,
    }

    _DIRECTION_MAP = {
        Action.MOVE_LEFT: 'left',
        Action.MOVE_RIGHT: 'right',
        Action.JUMP: 'up',
        Action.STOP: 'down',
    }

    def __init__(self, stdscr, seed: int | None = None):
        """Initialize game engine with curses screen."""
        self.stdscr = stdscr
        self.running = False

        # Initialize world
        self.world = World()
        self.generator = WorldGenerator(seed)
        self.generator.generate_world(self.world)

        # Initialize player at spawn point
        spawn_x, spawn_y = self.generator.get_spawn_position()
        self.player = Player(spawn_x, spawn_y)

        # Spawn mobs
        self.mobs = self.generator.spawn_mobs(self.world)

        # Initialize systems
        self.physics = PhysicsEngine(
            self.world, GRAVITY_INTERVAL, JUMP_HEIGHT,
            SAFE_FALL_DISTANCE, FALL_DAMAGE_PER_BLOCK,
        )
        self.renderer = Renderer(stdscr)
        self.input_handler = InputHandler()

        # Hotbar: 5 assignable slots, all start empty
        self._hotbar: list[BlockType | None] = [None] * self.HOTBAR_SIZE
        self._hotbar_index = 0

        # Pending action awaiting a direction key ('mine', 'place', or None)
        self._pending_action: str | None = None

        # Inventory overlay state
        self._inventory_open = False
        self._inventory_cursor = 0

        # Death screen timer (None = alive, >0 = showing death screen)
        self._death_timer: float | None = None
        self._death_duration = 2.0  # seconds to show death screen

    @property
    def selected_block(self) -> BlockType | None:
        return self._hotbar[self._hotbar_index]

    def run(self) -> None:
        """Run the main game loop."""
        self.running = True
        previous_time = time.time()
        accumulator = 0.0

        while self.running:
            current_time = time.time()
            frame_time = current_time - previous_time
            previous_time = current_time

            # Cap frame time to avoid spiral of death
            if frame_time > 0.25:
                frame_time = 0.25

            accumulator += frame_time

            if self._death_timer is not None:
                # Death screen active — count down, drain input, render
                self._death_timer -= frame_time
                self._drain_input()
                self.renderer.render_death_screen()
                if self._death_timer <= 0:
                    self._respawn()
            elif self._inventory_open:
                # Inventory screen — no physics, just handle inventory input
                self._handle_inventory_input()
                self._render()
            else:
                # Normal gameplay
                self._handle_input()

                while accumulator >= TICK_DURATION:
                    self._update(TICK_DURATION)
                    accumulator -= TICK_DURATION

                self._render()

            # Small sleep to prevent CPU spinning
            time.sleep(0.001)

    def _handle_input(self) -> None:
        """Process all pending input."""
        while True:
            key = self.renderer.get_key()
            if key == -1:
                break

            action = self.input_handler.process_key(key)

            if action == Action.QUIT:
                self.running = False
                return

            # If a mine/place is pending, the next direction key executes it
            if self._pending_action is not None:
                direction = self._DIRECTION_MAP.get(action)
                if direction is not None:
                    if self._pending_action == 'mine':
                        self._mine_block(direction)
                    else:
                        self._place_block(direction)
                    self._pending_action = None
                    continue

            # Hotbar selection
            if action in self._HOTBAR_SELECT:
                self._hotbar_index = self._HOTBAR_SELECT[action]
                continue
            if action == Action.HOTBAR_NEXT:
                self._hotbar_index = (self._hotbar_index + 1) % self.HOTBAR_SIZE
                continue
            if action == Action.HOTBAR_PREV:
                self._hotbar_index = (self._hotbar_index - 1) % self.HOTBAR_SIZE
                continue

            if action == Action.MOVE_LEFT:
                self.physics.try_move(self.player, -1, 0)
                self.player.facing_right = False
            elif action == Action.MOVE_RIGHT:
                self.physics.try_move(self.player, 1, 0)
                self.player.facing_right = True
            elif action == Action.JUMP:
                if self.player.on_ground:
                    self.player.jump_remaining = self.physics.jump_height
                    self.player.on_ground = False
            elif action == Action.MINE:
                self._pending_action = 'mine'
            elif action == Action.PLACE:
                self._pending_action = 'place'
            elif action == Action.INVENTORY:
                self._inventory_open = True

    def _update(self, dt: float) -> None:
        """Update game state for one tick."""
        self.physics.update(self.player, dt)

        # Update mobs
        for mob in self.mobs:
            if mob.is_alive:
                self.physics.update(mob, dt)
                dx = mob.update_ai(self.world, dt)
                if dx != 0:
                    self.physics.try_move(mob, dx, 0)

        # Trigger death screen
        if self.player.health <= 0 and self._death_timer is None:
            self._death_timer = self._death_duration

    def _respawn(self) -> None:
        """Reset player to spawn after death."""
        spawn_x, spawn_y = self.generator.get_spawn_position()
        self.player.x = spawn_x
        self.player.y = spawn_y
        self.player.health = 100
        self.player.fall_distance = 0
        self.player.jump_remaining = 0
        self.player.on_ground = False
        self._pending_action = None
        self._death_timer = None

    def _handle_inventory_input(self) -> None:
        """Process input while inventory overlay is open."""
        while True:
            key = self.renderer.get_key()
            if key == -1:
                break
            action = self.input_handler.process_key(key)
            if action == Action.INVENTORY:
                self._inventory_open = False
            elif action == Action.QUIT:
                self._inventory_open = False
            elif action == Action.JUMP:
                # W / Up = cursor up
                if self._inventory_cursor > 0:
                    self._inventory_cursor -= 1
            elif action == Action.STOP:
                # S / Down = cursor down
                items = self.player.inventory.items()
                if self._inventory_cursor < len(items) - 1:
                    self._inventory_cursor += 1
            elif action in self._HOTBAR_SELECT:
                # 1-5 assigns highlighted item to that hotbar slot
                items = self.player.inventory.items()
                if items and 0 <= self._inventory_cursor < len(items):
                    slot = self._HOTBAR_SELECT[action]
                    block_type = items[self._inventory_cursor][0]
                    # Toggle: if slot already has this type, clear it
                    if self._hotbar[slot] == block_type:
                        self._hotbar[slot] = None
                    else:
                        self._hotbar[slot] = block_type

    def _drain_input(self) -> None:
        """Consume all pending input without acting on it (still allow quit)."""
        while True:
            key = self.renderer.get_key()
            if key == -1:
                break
            action = self.input_handler.process_key(key)
            if action == Action.QUIT:
                self.running = False
                return

    def _render(self) -> None:
        """Render current game state."""
        if self._inventory_open:
            # Clamp cursor to valid range
            items = self.player.inventory.items()
            if items:
                self._inventory_cursor = min(self._inventory_cursor, len(items) - 1)
            else:
                self._inventory_cursor = 0
            self.renderer.render_inventory(
                self.player.inventory, self._hotbar,
                self._hotbar_index, self._inventory_cursor,
            )
        else:
            self.renderer.render(
                self.world, self.player, self._pending_action,
                self._hotbar, self._hotbar_index, self.mobs,
            )

    def _mine_block(self, direction: str) -> None:
        """Mine the first breakable block or attack a mob in the given direction."""
        for block_x, block_y in self.player.get_minable_positions_in_direction(direction):
            # Check for mobs at this position first
            for mob in self.mobs:
                if mob.is_alive and mob.x == block_x and mob.y == block_y:
                    mob.health -= 5
                    if not mob.is_alive:
                        for drop in mob.drops:
                            self.player.inventory.add(drop)
                        self.mobs.remove(mob)
                    return

            block = self.world.get_block(block_x, block_y)

            if block != BlockType.AIR:
                props = get_properties(block)
                if props.breakable:
                    self.world.set_block(block_x, block_y, BlockType.AIR)
                    # Add to inventory (leaves not collected, trunk gives wood)
                    if block == BlockType.TRUNK:
                        self.player.inventory.add(BlockType.WOOD)
                    elif block != BlockType.LEAVES:
                        self.player.inventory.add(block)
                    return  # Only mine one block per press

    def _place_block(self, direction: str) -> None:
        """Place a block in the given direction, consuming from inventory."""
        block = self.selected_block
        if block is None:
            return
        if self.player.inventory.count(block) <= 0:
            return

        block_x, block_y = self.player.get_block_in_direction(direction)
        current = self.world.get_block(block_x, block_y)

        # Only place in air or water, and not inside the player
        if current == BlockType.AIR or current == BlockType.WATER:
            if not (block_x == self.player.x and block_y == self.player.y):
                self.world.set_block(block_x, block_y, block)
                self.player.inventory.remove(block)
                # Clear hotbar slot if item depleted
                if self.player.inventory.count(block) <= 0:
                    self._hotbar[self._hotbar_index] = None
