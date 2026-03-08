"""Curses-based renderer for the game."""

from __future__ import annotations
import curses
from typing import Dict, List
from render.camera import Camera
from world.world import World
from world.block import BlockType, get_properties, display_name
from entity.player import Player
from entity.inventory import Inventory
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
               hotbar: List[BlockType | None] | None = None,
               hotbar_index: int = 0,
               mobs: list | None = None,
               save_flash: bool = False) -> None:
        """Render the current game state."""
        self.stdscr.erase()

        # Update camera to follow player
        self.camera.update(player)

        # Render world blocks
        self._render_world(world)

        # Render mobs (between world and player so player draws on top)
        if mobs:
            self._render_mobs(mobs)

        # Render player
        self._render_player(player)

        # Render HUD (top row)
        self._render_hud(player, hotbar or [], hotbar_index)

        # Render status bar (bottom row)
        self._render_status(player, pending_action, save_flash=save_flash)

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

    def _render_mobs(self, mobs: list) -> None:
        """Render mob entities."""
        for mob in mobs:
            if not mob.is_alive:
                continue
            col, row = self.camera.world_to_screen(mob.x, mob.y)
            screen_row = row + self.WORLD_ROW_OFFSET
            if 0 <= col < self.width and 0 <= row < self.view_height:
                mob_color = self.cfg.get_color(mob.color)
                color_pair = mob_color.pair_id if mob_color else 0
                try:
                    if curses.has_colors() and color_pair > 0:
                        self.stdscr.addch(
                            screen_row, col, mob.char,
                            curses.color_pair(color_pair) | curses.A_BOLD
                        )
                    else:
                        self.stdscr.addch(screen_row, col, mob.char, curses.A_BOLD)
                except curses.error:
                    pass

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

    def _render_hud(self, player: Player, hotbar: List[BlockType | None],
                    hotbar_index: int) -> None:
        """Render HUD row: health on the left, hotbar on the right."""
        row = self.HUD_ROW

        # --- Health (left side) ---
        heart = '\u2665'  # ♥
        hp_str = f" {heart} {player.health}"
        try:
            if curses.has_colors():
                self.stdscr.addstr(
                    row, 0, hp_str,
                    curses.color_pair(
                        self.cfg.get_color('red').pair_id
                    ) | curses.A_BOLD,
                )
            else:
                self.stdscr.addstr(row, 0, hp_str, curses.A_BOLD)
        except curses.error:
            pass

        # --- Hotbar (right side) ---
        if not hotbar:
            return

        # Build hotbar string and attribute spans
        # Format: 1[X] 2[ ] 3[X] ...
        slot_parts: list[tuple[str, int]] = []  # (text, curses_attr)
        for i, block_type in enumerate(hotbar):
            num = str(i + 1)

            if i == hotbar_index:
                attr = curses.A_REVERSE | curses.A_BOLD
            else:
                attr = curses.A_DIM

            slot_parts.append((num, attr))
            slot_parts.append(('[', attr))

            if block_type is not None:
                props = get_properties(block_type)
                block_attr = attr
                if curses.has_colors() and props.color_pair > 0:
                    block_attr |= curses.color_pair(props.color_pair)
                slot_parts.append((props.char, block_attr))
            else:
                slot_parts.append((' ', attr))

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
                       pending_action: str | None = None,
                       save_flash: bool = False) -> None:
        """Render status bar at bottom of screen."""
        if save_flash:
            status = " \u2713 World saved!  |  A/D:Move  W:Jump  M:Mine  P:Place  1-5/E/R:Hotbar  I:Inv  Q:Quit"
        elif pending_action is not None:
            label = pending_action.upper()
            status = f" {label} >> press direction (A/D/W/S)"
        else:
            status = f" Pos: ({player.x}, {player.y}) | "
            status += "A/D:Move  W:Jump  M:Mine  P:Place  1-5/E/R:Hotbar  I:Inv  Q:Quit"

        # Truncate if too long
        status = status[:self.width - 1]

        try:
            self.stdscr.addstr(self.height - 1, 0, status, curses.A_REVERSE)
        except curses.error:
            pass

    def render_inventory(self, inventory: Inventory,
                         hotbar: List[BlockType | None] | None = None,
                         hotbar_index: int = 0,
                         cursor: int = 0) -> None:
        """Render the inventory overlay screen."""
        self.stdscr.erase()

        hotbar = hotbar or [None] * 5

        # Box dimensions
        box_w = min(42, self.width - 2)
        box_h = min(22, self.height - 2)
        start_col = (self.width - box_w) // 2
        start_row = (self.height - box_h) // 2

        border_attr = curses.A_BOLD

        # Draw top border
        top = '+' + '-' * (box_w - 2) + '+'
        self._safe_addstr(start_row, start_col, top, border_attr)

        # Draw bottom border
        self._safe_addstr(start_row + box_h - 1, start_col, top, border_attr)

        # Draw side borders and fill interior with spaces
        for r in range(1, box_h - 1):
            line = '|' + ' ' * (box_w - 2) + '|'
            self._safe_addstr(start_row + r, start_col, line, border_attr)

        # Title
        title = 'INVENTORY'
        title_col = start_col + (box_w - len(title)) // 2
        self._safe_addstr(start_row + 1, title_col, title, curses.A_BOLD)

        # --- Hotbar display ---
        hotbar_label = '  Hotbar: '
        hb_row = start_row + 3
        hb_col = start_col + 2
        self._safe_addstr(hb_row, hb_col, hotbar_label, curses.A_BOLD)
        hb_col += len(hotbar_label)
        for i, slot in enumerate(hotbar):
            num = str(i + 1)
            if i == hotbar_index:
                attr = curses.A_REVERSE | curses.A_BOLD
            else:
                attr = 0
            self._safe_addstr(hb_row, hb_col, num, attr)
            self._safe_addstr(hb_row, hb_col + 1, '[', attr)
            if slot is not None:
                props = get_properties(slot)
                ch_attr = attr
                if curses.has_colors() and props.color_pair > 0:
                    ch_attr |= curses.color_pair(props.color_pair)
                self._safe_addstr(hb_row, hb_col + 2, props.char, ch_attr)
            else:
                self._safe_addstr(hb_row, hb_col + 2, ' ', attr)
            self._safe_addstr(hb_row, hb_col + 3, '] ', attr)
            hb_col += 5

        # --- Item list ---
        items = inventory.items()
        inner_w = box_w - 4  # padding inside borders
        items_start_row = start_row + 5

        if not items:
            msg = 'Empty'
            msg_col = start_col + (box_w - len(msg)) // 2
            self._safe_addstr(start_row + box_h // 2, msg_col, msg, curses.A_DIM)
        else:
            max_items = box_h - 8  # room for title, hotbar, footer, borders
            for i, (block_type, count) in enumerate(items):
                if i >= max_items:
                    break
                row = items_start_row + i
                col = start_col + 2

                props = get_properties(block_type)
                name = display_name(block_type)
                count_str = f'x {count}'

                # Cursor marker
                if i == cursor:
                    row_attr = curses.A_REVERSE
                    self._safe_addstr(row, col, '>', curses.A_BOLD)
                else:
                    row_attr = 0
                    self._safe_addstr(row, col, ' ')

                # block_char in its color
                char_attr = row_attr
                if curses.has_colors() and props.color_pair > 0:
                    char_attr |= curses.color_pair(props.color_pair)
                self._safe_addstr(row, col + 2, props.char, char_attr | curses.A_BOLD)

                # name + dots + count
                avail = inner_w - 4  # space after "> X "
                dots_len = avail - len(name) - 1 - len(count_str) - 1
                if dots_len < 1:
                    dots_len = 1
                dots = '.' * dots_len
                text = f' {name} {dots} {count_str}'
                self._safe_addstr(row, col + 3, text, row_attr)

        # Footer
        footer = '[W/S] Select  [1-5] Hotbar  [I] Close'
        footer_col = start_col + (box_w - len(footer)) // 2
        self._safe_addstr(start_row + box_h - 2, footer_col, footer, curses.A_DIM)

        self.stdscr.refresh()

    def _safe_addstr(self, row: int, col: int, text: str, attr: int = 0) -> None:
        """Write a string to screen, ignoring curses errors at edges."""
        try:
            self.stdscr.addstr(row, col, text, attr)
        except curses.error:
            pass

    def render_death_screen(self) -> None:
        """Render a full-screen death message."""
        self.stdscr.erase()

        msg = "YOU DIED"
        mid_row = self.height // 2
        mid_col = (self.width - len(msg)) // 2

        # Get red color
        red_pair = self.cfg.get_color('red').pair_id if self.cfg.get_color('red') else 0

        try:
            if curses.has_colors() and red_pair:
                attr = curses.color_pair(red_pair) | curses.A_BOLD
            else:
                attr = curses.A_BOLD
            self.stdscr.addstr(mid_row, mid_col, msg, attr)
        except curses.error:
            pass

        self.stdscr.refresh()

    def get_key(self) -> int:
        """Get key press (non-blocking)."""
        try:
            return self.stdscr.getch()
        except curses.error:
            return -1
