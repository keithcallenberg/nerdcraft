"""Curses-based renderer for the game."""

from __future__ import annotations
import curses
from typing import Dict, List
from render.camera import Camera
from world.world import World
from world.block import BlockType, get_properties
from entity.player import Player
from game.config import PLAYER_CHAR
from config import GameConfig


# Map color names to curses color constants
CURSES_COLORS: Dict[str, int] = {
    'default': -1,
    'black': curses.COLOR_BLACK,
    'red': curses.COLOR_RED,
    'green': curses.COLOR_GREEN,
    'yellow': curses.COLOR_YELLOW,
    'blue': curses.COLOR_BLUE,
    'magenta': curses.COLOR_MAGENTA,
    'cyan': curses.COLOR_CYAN,
    'white': curses.COLOR_WHITE,
}


class Renderer:
    """Renders the game world using curses."""

    # Row 0 = HUD, rows 1..height-2 = game world, row height-1 = status bar
    HUD_ROW = 0
    WORLD_ROW_OFFSET = 1

    def __init__(self, stdscr):
        """Initialize renderer with curses screen."""
        self.stdscr = stdscr
        self.cfg = GameConfig.get()
        self._setup_curses()
        self._init_colors()

        # Get screen size
        self.height, self.width = stdscr.getmaxyx()
        # Reserve top row for HUD and bottom row for status
        self.view_height = self.height - 2

        self.camera = Camera(self.width, self.view_height)

    def _setup_curses(self) -> None:
        """Configure curses settings."""
        curses.curs_set(0)  # Hide cursor
        self.stdscr.nodelay(True)  # Non-blocking input
        self.stdscr.keypad(True)  # Enable special keys

    def _init_colors(self) -> None:
        """Initialize color pairs from JSON configuration."""
        if not curses.has_colors():
            return

        curses.start_color()
        curses.use_default_colors()

        # Initialize color pairs from config
        for name, color_cfg in self.cfg.colors.items():
            if color_cfg.pair_id == 0:
                continue  # Skip default pair (reserved)

            fg = CURSES_COLORS.get(color_cfg.foreground, -1)
            bg = CURSES_COLORS.get(color_cfg.background, -1)

            try:
                curses.init_pair(color_cfg.pair_id, fg, bg)
            except curses.error:
                pass  # Some color pairs may not be supported

    def render(self, world: World, player: Player,
               pending_action: str | None = None,
               hotbar: List[BlockType] | None = None,
               hotbar_index: int = 0) -> None:
        """Render the current game state."""
        self.stdscr.erase()

        # Update camera to follow player
        self.camera.update(player)

        # Render world blocks
        self._render_world(world)

        # Render player
        self._render_player(player)

        # Render HUD (top row)
        self._render_hud(player, hotbar or [], hotbar_index)

        # Render status bar (bottom row)
        self._render_status(player, pending_action)

        self.stdscr.refresh()

    def _render_world(self, world: World) -> None:
        """Render visible world blocks."""
        for view_row in range(self.view_height):
            screen_row = view_row + self.WORLD_ROW_OFFSET
            for col in range(self.width):
                world_x, world_y = self.camera.screen_to_world(col, view_row)
                block = world.get_block(world_x, world_y)

                if block != BlockType.AIR:
                    props = get_properties(block)
                    try:
                        if curses.has_colors() and props.color_pair > 0:
                            self.stdscr.addch(
                                screen_row, col, props.char,
                                curses.color_pair(props.color_pair)
                            )
                        else:
                            self.stdscr.addch(screen_row, col, props.char)
                    except curses.error:
                        pass  # Ignore errors at screen edges

    def _render_player(self, player: Player) -> None:
        """Render the player character."""
        col, row = self.camera.world_to_screen(player.x, player.y)
        screen_row = row + self.WORLD_ROW_OFFSET

        # Get player color from config
        player_color = self.cfg.get_color('red')
        color_pair = player_color.pair_id if player_color else 8

        # Render player at their position
        if 0 <= col < self.width and 0 <= row < self.view_height:
            try:
                if curses.has_colors():
                    self.stdscr.addch(
                        screen_row, col, PLAYER_CHAR,
                        curses.color_pair(color_pair) | curses.A_BOLD
                    )
                else:
                    self.stdscr.addch(screen_row, col, PLAYER_CHAR, curses.A_BOLD)
            except curses.error:
                pass

    def _render_hud(self, player: Player, hotbar: List[BlockType],
                    hotbar_index: int) -> None:
        """Render HUD row: lives on the left, hotbar on the right."""
        row = self.HUD_ROW

        # --- Lives (left side) ---
        heart = '\u2665'  # ♥
        lives_str = f" {heart * player.lives}"
        try:
            if curses.has_colors():
                self.stdscr.addstr(
                    row, 0, lives_str,
                    curses.color_pair(
                        self.cfg.get_color('red').pair_id
                    ) | curses.A_BOLD,
                )
            else:
                self.stdscr.addstr(row, 0, lives_str, curses.A_BOLD)
        except curses.error:
            pass

        # --- Hotbar (right side) ---
        if not hotbar:
            return

        # Build hotbar string and attribute spans
        # Format: 1[X] 2[X] 3[X] ...
        slot_parts: list[tuple[str, int]] = []  # (text, curses_attr)
        for i, block_type in enumerate(hotbar):
            props = get_properties(block_type)
            num = str(i + 1)
            block_char = props.char

            if i == hotbar_index:
                # Selected slot: highlighted
                attr = curses.A_REVERSE | curses.A_BOLD
            else:
                attr = curses.A_DIM

            # Number label
            slot_parts.append((num, attr))
            # Opening bracket
            slot_parts.append(('[', attr))
            # Block character in its own color
            block_attr = attr
            if curses.has_colors() and props.color_pair > 0:
                block_attr |= curses.color_pair(props.color_pair)
            slot_parts.append((block_char, block_attr))
            # Closing bracket + space
            slot_parts.append(('] ', attr))

        # Calculate total width to right-align
        total_len = sum(len(text) for text, _ in slot_parts)
        start_col = self.width - total_len - 1
        if start_col < 0:
            start_col = 0

        col = start_col
        for text, attr in slot_parts:
            if col + len(text) > self.width:
                break
            try:
                self.stdscr.addstr(row, col, text, attr)
            except curses.error:
                pass
            col += len(text)

    def _render_status(self, player: Player,
                       pending_action: str | None = None) -> None:
        """Render status bar at bottom of screen."""
        if pending_action is not None:
            label = pending_action.upper()
            status = f" {label} >> press direction (A/D/W/S)"
        else:
            status = f" Pos: ({player.x}, {player.y}) | "
            status += "A/D:Move  W:Jump  M:Mine  P:Place  1-5/E/R:Hotbar  Q:Quit"

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
