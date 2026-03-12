"""Main game engine with fixed-timestep game loop."""

from __future__ import annotations
import curses
import time
from pathlib import Path

from game.config import (
    TICK_DURATION, GRAVITY_INTERVAL, JUMP_HEIGHT,
    SAFE_FALL_DISTANCE, FALL_DAMAGE_PER_BLOCK,
)
from world.world import World
from world.block import BlockType, get_properties
from world.generator import WorldGenerator
from world.save import SaveManager
from entity.player import Player
from entity.physics import PhysicsEngine
from entity.crafting import RecipeEngine
from entity.inventory import InventoryType
from entity.item import ItemType, ItemClass, get_item_properties
from render.renderer import Renderer
from input.handler import InputHandler, Action
from config import GameConfig
from game.clock import DayClock
from game.sound import SoundManager, SoundEvent
from game.music import AmbientMusic


class GameEngine:
    """Main game engine orchestrating all systems."""

    HOTBAR_SIZE = 5

    # Mining tier requirements by block type.
    # 0=fist/basic, 1=wood pick, 2=stone pick, 3=iron pick
    _MINING_TIER_REQUIRED = {
        BlockType.STONE: 1,
        BlockType.COAL_ORE: 1,
        BlockType.IRON_ORE: 2,
        BlockType.GOLD_ORE: 3,
        BlockType.DIAMOND_ORE: 3,
    }

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

    def __init__(self, stdscr, seed: int | None = None,
                 save_name: str = "default", force_new: bool = False):
        """Initialize game engine with curses screen."""
        self.stdscr = stdscr
        self.running = False
        self._cfg = GameConfig.get()

        # Save/load setup
        self._save_manager = SaveManager(
            save_dir=self._cfg.save.save_dir,
            save_name=save_name,
        )
        self._auto_save_ticks = self._cfg.save.auto_save_ticks
        self._ticks_since_save = 0
        self._save_flash: float = 0.0   # seconds remaining for "Saved!" flash
        self._save_flash_duration = 2.0

        # Initialize world and player
        self.world = World()
        self.player = Player()

        if not force_new and self._save_manager.save_exists():
            # Load existing save
            loaded_seed = self._save_manager.load(self.world, self.player)
            self.generator = WorldGenerator(loaded_seed)
            # Spawn mobs fresh (mobs are not saved for now)
            self.mobs = self.generator.spawn_mobs(self.world)
        else:
            # Generate a fresh world
            self.generator = WorldGenerator(seed)
            self.generator.generate_world(self.world)
            spawn_x, spawn_y = self.generator.get_spawn_position()
            self.player.x = spawn_x
            self.player.y = spawn_y
            self.mobs = self.generator.spawn_mobs(self.world)

        # Initialize systems
        self.clock = DayClock(day_length_ticks=self._cfg.day_length_ticks)
        self.physics = PhysicsEngine(
            self.world, GRAVITY_INTERVAL, JUMP_HEIGHT,
            SAFE_FALL_DISTANCE, FALL_DAMAGE_PER_BLOCK,
        )
        self.renderer = Renderer(stdscr)
        self.input_handler = InputHandler()
        self.sound = SoundManager()
        self.music = AmbientMusic()

        # Hotbar: 5 assignable slots, all start empty
        self._hotbar: list[InventoryType | None] = [None] * self.HOTBAR_SIZE
        self._hotbar_index = 0

        # Inventory overlay state
        self._inventory_open = False
        self._inventory_cursor = 0

        # Crafting overlay state
        self._recipe_engine = RecipeEngine()
        self._crafting_open = False
        self._crafting_cursor = 0

        # Death screen timer (None = alive, >0 = showing death screen)
        self._death_timer: float | None = None
        self._death_duration = 2.0  # seconds to show death screen

        # Short status feedback for failed actions, etc.
        self._status_flash: str | None = None
        self._status_flash_timer: float = 0.0

        # Night spawn pacing for hostile, night_only surface mobs
        self._night_spawn_interval_ticks = 900
        self._ticks_since_night_spawn = 0
        self._night_spawn_cap = 18

    @property
    def selected_item(self) -> InventoryType | None:
        return self._hotbar[self._hotbar_index]

    def run(self) -> None:
        """Run the main game loop."""
        self.running = True
        previous_time = time.time()
        accumulator = 0.0
        self.music.start()

        try:
            while self.running:
                current_time = time.time()
                frame_time = current_time - previous_time
                previous_time = current_time

                # Cap frame time to avoid spiral of death
                if frame_time > 0.25:
                    frame_time = 0.25

                accumulator += frame_time

                # Tick save flash timer
                if self._save_flash > 0:
                    self._save_flash -= frame_time

                if self._status_flash_timer > 0:
                    self._status_flash_timer -= frame_time
                    if self._status_flash_timer <= 0:
                        self._status_flash = None

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
                elif self._crafting_open:
                    # Crafting screen — no physics, just handle crafting input
                    self._handle_crafting_input()
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
        finally:
            self.music.stop()
            # Save on clean exit
            self._do_save()

    def _do_save(self) -> None:
        """Perform a save and reset the auto-save counter."""
        try:
            self._save_manager.save(self.world, self.player, self.generator.seed)
            self._ticks_since_save = 0
            self._save_flash = self._save_flash_duration
        except Exception:
            pass  # Don't crash on save failure

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
                if self.physics.try_move(self.player, -1, 0):
                    self.sound.play(SoundEvent.FOOTSTEP)
                self.player.facing_right = False
            elif action == Action.MOVE_RIGHT:
                if self.physics.try_move(self.player, 1, 0):
                    self.sound.play(SoundEvent.FOOTSTEP)
                self.player.facing_right = True
            elif action == Action.JUMP:
                if self.player.on_ground:
                    self.player.jump_remaining = self.physics.jump_height
                    self.player.on_ground = False
            elif action == Action.USE:
                self._use_selected()
            elif action == Action.INVENTORY:
                self._inventory_open = True
            elif action == Action.CRAFT:
                self._crafting_open = True

    def _update(self, dt: float) -> None:
        """Update game state for one tick."""
        self.physics.update(self.player, dt)
        self.clock.tick()

        # Update mobs
        dead_mobs = []
        for mob in self.mobs:
            if not mob.is_alive:
                dead_mobs.append(mob)
                continue

            self.physics.update(mob, dt)
            dx = mob.update_ai(
                self.world, dt,
                player_x=self.player.x,
                player_y=self.player.y,
            )
            if dx != 0:
                self.physics.try_move(mob, dx, 0)

            # Hostile mob attacks player when adjacent
            if mob.hostile and self.player.health > 0:
                dist_x = abs(mob.x - self.player.x)
                dist_y = abs(mob.y - self.player.y)
                if dist_x <= 1 and dist_y <= 1 and mob.can_attack_now():
                    damage = mob.get_attack_damage()
                    self.player.health = max(0, self.player.health - damage)
                    self.sound.play(SoundEvent.HIT)
                    mob.reset_attack_timer()

        # Remove dead mobs and collect their drops
        for mob in dead_mobs:
            self.mobs.remove(mob)

        # Night-only hostile surface spawns
        if self.clock.is_night:
            self._ticks_since_night_spawn += 1
            if (
                self._ticks_since_night_spawn >= self._night_spawn_interval_ticks
                and len(self.mobs) < self._night_spawn_cap
            ):
                self._ticks_since_night_spawn = 0
                occupied = {(self.player.x, self.player.y)}
                occupied.update((mob.x, mob.y) for mob in self.mobs if mob.is_alive)
                spawned = self.generator.spawn_night_hostile(self.world, occupied)
                if spawned is not None and abs(spawned.x - self.player.x) >= 12:
                    self.mobs.append(spawned)
        else:
            self._ticks_since_night_spawn = 0

        # Trigger death screen
        if self.player.health <= 0 and self._death_timer is None:
            self.sound.play(SoundEvent.DEATH)
            self._death_timer = self._death_duration

        # Auto-save
        self._ticks_since_save += 1
        if self._ticks_since_save >= self._auto_save_ticks:
            self._do_save()

    def _respawn(self) -> None:
        """Reset player to spawn after death."""
        spawn_x, spawn_y = self.generator.get_spawn_position()
        self.player.x = spawn_x
        self.player.y = spawn_y
        self.player.health = 100
        self.player.fall_distance = 0
        self.player.jump_remaining = 0
        self.player.on_ground = False
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

    def _handle_crafting_input(self) -> None:
        """Process input while crafting overlay is open."""
        while True:
            key = self.renderer.get_key()
            if key == -1:
                break

            action = self.input_handler.process_key(key)
            recipes = self._recipe_engine.available_recipes(self.player.inventory)

            if action == Action.CRAFT:
                self._crafting_open = False
            elif action == Action.QUIT:
                self._crafting_open = False
            elif action == Action.JUMP:
                # W / Up = cursor up
                if self._crafting_cursor > 0:
                    self._crafting_cursor -= 1
            elif action == Action.STOP:
                # S / Down = cursor down
                if self._crafting_cursor < len(recipes) - 1:
                    self._crafting_cursor += 1
            elif key in (10, 13, curses.KEY_ENTER, ord(' ')):
                # Enter / Space = craft selected recipe
                if recipes and 0 <= self._crafting_cursor < len(recipes):
                    recipe = recipes[self._crafting_cursor]
                    self._recipe_engine.craft(self.player.inventory, recipe.recipe_id)
                    refreshed = self._recipe_engine.available_recipes(self.player.inventory)
                    if refreshed:
                        self._crafting_cursor = min(self._crafting_cursor, len(refreshed) - 1)
                    else:
                        self._crafting_cursor = 0

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
        elif self._crafting_open:
            recipes = self._recipe_engine.available_recipes(self.player.inventory)
            if recipes:
                self._crafting_cursor = min(self._crafting_cursor, len(recipes) - 1)
            else:
                self._crafting_cursor = 0
            self.renderer.render_crafting(
                self.player.inventory,
                recipes,
                self._crafting_cursor,
            )
        else:
            self.renderer.render(
                self.world, self.player,
                self._hotbar, self._hotbar_index, self.mobs,
                save_flash=self._save_flash > 0,
                is_night=self.clock.is_night,
                time_icon=self.clock.hud_icon,
                status_message=self._status_flash,
            )

    def _set_status_flash(self, message: str, duration: float = 1.2) -> None:
        self._status_flash = message
        self._status_flash_timer = duration

    def _facing_direction(self) -> str:
        return 'right' if self.player.facing_right else 'left'

    def _use_selected(self) -> None:
        """Use selected hotbar item, or fallback to fist mining/attack."""
        selected = self.selected_item
        direction = self._facing_direction()

        if selected is None:
            self._mine_block(direction, attack_damage=5, mining_tier=0)
            return

        if isinstance(selected, ItemType):
            props = get_item_properties(selected)
            if props.item_class == ItemClass.CONSUMABLE:
                if self.player.inventory.remove(selected):
                    self.player.health = min(100, self.player.health + props.heal_amount)
                    if self.player.inventory.count(selected) <= 0:
                        self._hotbar[self._hotbar_index] = None
                return

            if props.item_class == ItemClass.WEAPON:
                self._mine_block(
                    direction,
                    attack_damage=max(1, props.attack_damage),
                    mining_tier=0,
                    allow_block_break=False,
                )
                return

            if props.item_class == ItemClass.TOOL:
                self._mine_block(
                    direction,
                    attack_damage=5,
                    mining_tier=props.mining_tier,
                )
                return

            return

        # Blocks remain placeable for now.
        self._place_block(direction, selected)

    def _mine_block(
        self,
        direction: str,
        attack_damage: int = 5,
        mining_tier: int = 0,
        allow_block_break: bool = True,
    ) -> None:
        """Mine the first breakable block or attack a mob in the given direction."""
        for block_x, block_y in self.player.get_minable_positions_in_direction(direction):
            # Check for mobs at this position first
            for mob in self.mobs:
                if mob.is_alive and mob.x == block_x and mob.y == block_y:
                    mob.health -= attack_damage
                    self.sound.play(SoundEvent.MINING)
                    if not mob.is_alive:
                        for drop in mob.drops:
                            self.player.inventory.add(drop)
                        self.mobs.remove(mob)
                    return

            block = self.world.get_block(block_x, block_y)

            if block != BlockType.AIR:
                if not allow_block_break:
                    return

                props = get_properties(block)
                if props.breakable:
                    required_tier = self._MINING_TIER_REQUIRED.get(block, 0)
                    if mining_tier < required_tier:
                        if required_tier == 1:
                            needed = "wood pickaxe"
                        elif required_tier == 2:
                            needed = "stone pickaxe"
                        else:
                            needed = "iron pickaxe"
                        self._set_status_flash(f"Need {needed} for {block.name.lower()}")
                        return

                    self.world.set_block(block_x, block_y, BlockType.AIR)
                    # Add to inventory (leaves not collected, trunk gives wood)
                    if block == BlockType.TRUNK:
                        self.player.inventory.add(BlockType.WOOD)
                    elif block == BlockType.LEAVES:
                        # Early non-block item drop support
                        import random

                        if random.random() < 0.12:
                            self.player.inventory.add(ItemType.APPLE)
                    else:
                        self.player.inventory.add(block)
                    self.sound.play(SoundEvent.MINING)
                    return  # Only mine one block per press

    def _place_block(self, direction: str, block: BlockType) -> None:
        """Place a block in the given direction, consuming from inventory."""
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
