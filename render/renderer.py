"""Curses-based renderer for the game."""

from __future__ import annotations
import curses
from render.camera import Camera
from world.world import World
from world.block import BlockType, get_properties
from entity.player import Player
from game.config import PLAYER_CHAR


class Renderer:
    """Renders the game world using curses."""

    def __init__(self, stdscr):
        """Initialize renderer with curses screen."""
        self.stdscr = stdscr
        self._setup_curses()
        self._init_colors()

        # Get screen size
        self.height, self.width = stdscr.getmaxyx()
        # Reserve bottom line for status
        self.view_height = self.height - 1

        self.camera = Camera(self.width, self.view_height)

    def _setup_curses(self) -> None:
        """Configure curses settings."""
        curses.curs_set(0)  # Hide cursor
        self.stdscr.nodelay(True)  # Non-blocking input
        self.stdscr.keypad(True)  # Enable special keys

    def _init_colors(self) -> None:
        """Initialize color pairs for block types."""
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()

            # Color pairs: (pair_id, foreground, background)
            # 0: default (reserved)
            # 1: grass (green)
            curses.init_pair(1, curses.COLOR_GREEN, -1)
            # 2: dirt (yellow/brown)
            curses.init_pair(2, curses.COLOR_YELLOW, -1)
            # 3: stone (white)
            curses.init_pair(3, curses.COLOR_WHITE, -1)
            # 4: coal (dark gray - use blue as fallback)
            curses.init_pair(4, curses.COLOR_BLUE, -1)
            # 5: iron (cyan)
            curses.init_pair(5, curses.COLOR_CYAN, -1)
            # 6: gold (yellow)
            curses.init_pair(6, curses.COLOR_YELLOW, -1)
            # 7: diamond (cyan/bright)
            curses.init_pair(7, curses.COLOR_CYAN, -1)
            # 8: player (red)
            curses.init_pair(8, curses.COLOR_RED, -1)

    def render(self, world: World, player: Player) -> None:
        """Render the current game state."""
        self.stdscr.erase()

        # Update camera to follow player
        self.camera.update(player)

        # Render world blocks
        self._render_world(world)

        # Render player
        self._render_player(player)

        # Render status bar
        self._render_status(player)

        self.stdscr.refresh()

    def _render_world(self, world: World) -> None:
        """Render visible world blocks."""
        for row in range(self.view_height):
            for col in range(self.width):
                world_x, world_y = self.camera.screen_to_world(col, row)
                block = world.get_block(world_x, world_y)

                if block != BlockType.AIR:
                    props = get_properties(block)
                    try:
                        if curses.has_colors() and props.color_pair > 0:
                            self.stdscr.addch(
                                row, col, props.char,
                                curses.color_pair(props.color_pair)
                            )
                        else:
                            self.stdscr.addch(row, col, props.char)
                    except curses.error:
                        pass  # Ignore errors at screen edges

    def _render_player(self, player: Player) -> None:
        """Render the player character."""
        col, row = self.camera.world_to_screen(player.x, player.y)

        # Render player at their position (may span multiple rows due to height)
        if 0 <= col < self.width and 0 <= row < self.view_height:
            try:
                if curses.has_colors():
                    self.stdscr.addch(
                        row, col, PLAYER_CHAR,
                        curses.color_pair(8) | curses.A_BOLD
                    )
                else:
                    self.stdscr.addch(row, col, PLAYER_CHAR, curses.A_BOLD)
            except curses.error:
                pass

    def _render_status(self, player: Player) -> None:
        """Render status bar at bottom of screen."""
        status = f" Pos: ({player.x:.1f}, {player.y:.1f}) | "
        status += f"Ground: {'Yes' if player.on_ground else 'No'} | "
        status += f"Facing: {'Right' if player.facing_right else 'Left'} | "
        status += "A/D:Move  S:Stop  W/Space:Jump  M:Mine  P:Place  Q:Quit"

        # Truncate if too long
        status = status[:self.width - 1]

        try:
            self.stdscr.addstr(self.height - 1, 0, status, curses.A_REVERSE)
        except curses.error:
            pass

    def get_key(self) -> int:
        """Get key press (non-blocking)."""
        try:
            return self.stdscr.getch()
        except curses.error:
            return -1
