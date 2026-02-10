"""Main game engine with fixed-timestep game loop."""

from __future__ import annotations
import time
from game.config import TICK_DURATION, GRAVITY_INTERVAL, JUMP_HEIGHT
from world.world import World
from world.block import BlockType, get_properties
from world.generator import WorldGenerator
from entity.player import Player
from entity.physics import PhysicsEngine
from render.renderer import Renderer
from input.handler import InputHandler, Action


class GameEngine:
    """Main game engine orchestrating all systems."""

    HOTBAR = [
        BlockType.CONCRETE,
        BlockType.DIRT,
        BlockType.STONE,
        BlockType.GRASS,
        BlockType.WOOD,
    ]

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

        # Initialize systems
        self.physics = PhysicsEngine(self.world, GRAVITY_INTERVAL, JUMP_HEIGHT)
        self.renderer = Renderer(stdscr)
        self.input_handler = InputHandler()

        # Hotbar
        self._hotbar_index = 0

        # Pending action awaiting a direction key ('mine', 'place', or None)
        self._pending_action: str | None = None

    @property
    def selected_block(self) -> BlockType:
        return self.HOTBAR[self._hotbar_index]

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
                self._hotbar_index = (self._hotbar_index + 1) % len(self.HOTBAR)
                continue
            if action == Action.HOTBAR_PREV:
                self._hotbar_index = (self._hotbar_index - 1) % len(self.HOTBAR)
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

    def _update(self, dt: float) -> None:
        """Update game state for one tick."""
        self.physics.update(self.player, dt)

    def _render(self) -> None:
        """Render current game state."""
        self.renderer.render(
            self.world, self.player, self._pending_action,
            self.HOTBAR, self._hotbar_index,
        )

    def _mine_block(self, direction: str) -> None:
        """Mine the first breakable block in the given direction."""
        for block_x, block_y in self.player.get_minable_positions_in_direction(direction):
            block = self.world.get_block(block_x, block_y)

            if block != BlockType.AIR:
                props = get_properties(block)
                if props.breakable:
                    self.world.set_block(block_x, block_y, BlockType.AIR)
                    return  # Only mine one block per press

    def _place_block(self, direction: str) -> None:
        """Place a block in the given direction."""
        block_x, block_y = self.player.get_block_in_direction(direction)
        current = self.world.get_block(block_x, block_y)

        # Only place in air or water, and not inside the player
        if current == BlockType.AIR or current == BlockType.WATER:
            if not (block_x == self.player.x and block_y == self.player.y):
                self.world.set_block(block_x, block_y, self.selected_block)
