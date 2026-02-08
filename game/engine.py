"""Main game engine with fixed-timestep game loop."""

from __future__ import annotations
from typing import Optional
import time
from game.config import TICK_DURATION
from world.world import World
from world.block import BlockType, get_properties
from world.generator import WorldGenerator
from entity.player import Player
from entity.physics import PhysicsEngine
from render.renderer import Renderer
from input.handler import InputHandler, Action


class GameEngine:
    """Main game engine orchestrating all systems."""

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

        # Initialize systems
        self.physics = PhysicsEngine(self.world)
        self.renderer = Renderer(stdscr)
        self.input_handler = InputHandler()

        # Currently selected block for placement
        self.selected_block = BlockType.DIRT

        # Movement state: -1 = left, 0 = stopped, 1 = right
        self._move_direction = 0

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

            # Process input
            self._handle_input()

            # Fixed timestep updates
            while accumulator >= TICK_DURATION:
                self._update(TICK_DURATION)
                accumulator -= TICK_DURATION

            # Render
            self._render()

            # Small sleep to prevent CPU spinning
            time.sleep(0.001)

    def _handle_input(self) -> None:
        """Process all pending input."""
        # Process all queued keys
        while True:
            key = self.renderer.get_key()
            if key == -1:
                break

            action = self.input_handler.process_key(key)

            if action == Action.QUIT:
                self.running = False
                return
            elif action == Action.MOVE_LEFT:
                self._move_direction = -1
            elif action == Action.MOVE_RIGHT:
                self._move_direction = 1
            elif action == Action.STOP:
                self._move_direction = 0
            elif action == Action.JUMP:
                self.player.jump()
            elif action == Action.MINE:
                self._mine_block()
            elif action == Action.PLACE:
                self._place_block()

        # Apply current movement direction
        if self._move_direction < 0:
            self.player.move_left()
        elif self._move_direction > 0:
            self.player.move_right()
        else:
            self.player.stop_horizontal()

    def _update(self, dt: float) -> None:
        """Update game state for one tick."""
        self.physics.update(self.player, dt)

    def _render(self) -> None:
        """Render current game state."""
        self.renderer.render(self.world, self.player)

    def _mine_block(self) -> None:
        """Mine the block in front of the player."""
        block_x, block_y = self.player.get_block_in_front()
        block = self.world.get_block(block_x, block_y)

        if block != BlockType.AIR:
            props = get_properties(block)
            if props.breakable:
                self.world.set_block(block_x, block_y, BlockType.AIR)

    def _place_block(self) -> None:
        """Place a block in front of the player."""
        block_x, block_y = self.player.get_block_in_front()
        current = self.world.get_block(block_x, block_y)

        # Only place in air
        if current == BlockType.AIR:
            # Check we're not placing inside the player
            left, bottom, right, top = self.player.get_aabb()
            player_min_x = int(left)
            player_max_x = int(right)
            player_min_y = int(bottom)
            player_max_y = int(top)

            # Don't place if it would intersect player
            if not (player_min_x <= block_x <= player_max_x and
                    player_min_y <= block_y <= player_max_y):
                self.world.set_block(block_x, block_y, self.selected_block)
