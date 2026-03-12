"""Curses-based renderer for the game."""

from __future__ import annotations
import curses
from typing import Dict, List, Any
from render.camera import Camera
from world.world import World
from world.block import BlockType, get_properties, display_name
from entity.player import Player
from entity.inventory import Inventory, InventoryType
from entity.item import ItemType, get_item_properties, item_display_name
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
               hotbar: List[InventoryType | None] | None = None,
               hotbar_index: int = 0,
               mobs: list | None = None,
               save_flash: bool = False,
               is_night: bool = False,
               time_icon: str = "",
               status_message: str | None = None) -> None:
        """Render the current game state."""
        self.stdscr.erase()

        # Update camera to follow player
        self.camera.update(player)

        # Render world blocks
        self._render_world(world, is_night=is_night)

        # Render mobs (between world and player so player draws on top)
        if mobs:
            self._render_mobs(mobs)

        # Render player
        self._render_player(player)

        # Render HUD (top row)
        self._render_hud(player, hotbar or [], hotbar_index, time_icon=time_icon)

        # Render status bar (bottom row)
        self._render_status(player, save_flash=save_flash, status_message=status_message)

        self.stdscr.refresh()

    def _render_world(self, world: World, is_night: bool = False) -> None:
        """Render visible world blocks."""
        light_sources = self._collect_visible_light_sources(world) if is_night else []

        for view_row in range(self.view_height):
            screen_row = view_row + self.WORLD_ROW_OFFSET
            for col in range(self.width):
                world_x, world_y = self.camera.screen_to_world(col, view_row)
                block = world.get_block(world_x, world_y)

                if block != BlockType.AIR:
                    props = get_properties(block)
                    try:
                        is_lit = self._is_lit(world_x, world_y, light_sources)
                        attr = curses.A_NORMAL if (not is_night or is_lit) else curses.A_DIM
                        if curses.has_colors() and props.color_pair > 0:
                            attr |= curses.color_pair(props.color_pair)
                        self.stdscr.addch(screen_row, col, props.char, attr)
                    except curses.error:
                        pass  # Ignore errors at screen edges

    def _collect_visible_light_sources(self, world: World) -> list[tuple[int, int, int]]:
        """Collect light-emitting blocks around the viewport."""
        max_radius = get_properties(BlockType.TORCH).light_radius
        if max_radius <= 0:
            return []

        left_x, top_y = self.camera.screen_to_world(0, 0)
        right_x, bottom_y = self.camera.screen_to_world(self.width - 1, self.view_height - 1)

        sources: list[tuple[int, int, int]] = []
        for y in range(top_y - max_radius, bottom_y + max_radius + 1):
            for x in range(left_x - max_radius, right_x + max_radius + 1):
                block = world.get_block(x, y)
                if block == BlockType.AIR:
                    continue
                radius = get_properties(block).light_radius
                if radius > 0:
                    sources.append((x, y, radius))
        return sources

    @staticmethod
    def _is_lit(x: int, y: int, sources: list[tuple[int, int, int]]) -> bool:
        """Return True when a world position is within any light source radius."""
        for sx, sy, radius in sources:
            dx = x - sx
            dy = y - sy
            if (dx * dx + dy * dy) <= (radius * radius):
                return True
        return False

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

    def _render_hud(self, player: Player, hotbar: List[InventoryType | None],
                    hotbar_index: int, time_icon: str = "") -> None:
        """Render HUD row: health on the left, hotbar on the right."""
        row = self.HUD_ROW

        # --- Health (left side) ---
        heart = '\u2665'  # ♥
        if time_icon:
            hp_str = f" {heart} {player.health}  {time_icon}"
        else:
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
                block_attr = attr
                if isinstance(block_type, BlockType):
                    props = get_properties(block_type)
                    if curses.has_colors() and props.color_pair > 0:
                        block_attr |= curses.color_pair(props.color_pair)
                    slot_parts.append((props.char, block_attr))
                else:
                    props = get_item_properties(block_type)
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
                       save_flash: bool = False,
                       status_message: str | None = None) -> None:
        """Render status bar at bottom of screen."""
        if status_message:
            status = f" {status_message}"
        elif save_flash:
            status = " \u2713 World saved!  |  A/D:Move  W:Jump  Space:Use  1-5/E/R:Hotbar  I:Inv  C:Craft  Q:Quit"
        else:
            status = f" Pos: ({player.x}, {player.y}) | "
            status += "A/D:Move  W:Jump  Space:Use  1-5/E/R:Hotbar  I:Inv  C:Craft  Q:Quit"

        # Truncate if too long
        status = status[:self.width - 1]

        try:
            self.stdscr.addstr(self.height - 1, 0, status, curses.A_REVERSE)
        except curses.error:
            pass

    def render_inventory(self, inventory: Inventory,
                         hotbar: List[InventoryType | None] | None = None,
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
                ch_attr = attr
                if isinstance(slot, BlockType):
                    props = get_properties(slot)
                    if curses.has_colors() and props.color_pair > 0:
                        ch_attr |= curses.color_pair(props.color_pair)
                    self._safe_addstr(hb_row, hb_col + 2, props.char, ch_attr)
                else:
                    props = get_item_properties(slot)
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

            # Scroll window to keep cursor visible in long inventories.
            total_items = len(items)
            max_start = max(0, total_items - max_items)
            visible_start = min(max_start, max(0, cursor - max_items + 1))
            visible_items = items[visible_start:visible_start + max_items]

            for visible_i, (item_type, count) in enumerate(visible_items):
                absolute_i = visible_start + visible_i
                row = items_start_row + visible_i
                col = start_col + 2

                if isinstance(item_type, BlockType):
                    props = get_properties(item_type)
                    name = display_name(item_type)
                    color_pair = props.color_pair
                    item_char = props.char
                else:
                    props = get_item_properties(item_type)
                    name = item_display_name(item_type)
                    color_pair = 0
                    item_char = props.char
                count_str = f'x {count}'

                # Cursor marker
                if absolute_i == cursor:
                    row_attr = curses.A_REVERSE
                    self._safe_addstr(row, col, '>', curses.A_BOLD)
                else:
                    row_attr = 0
                    self._safe_addstr(row, col, ' ')

                # block_char in its color
                char_attr = row_attr
                if curses.has_colors() and color_pair > 0:
                    char_attr |= curses.color_pair(color_pair)
                self._safe_addstr(row, col + 2, item_char, char_attr | curses.A_BOLD)

                # name + dots + count
                avail = inner_w - 4  # space after "> X "
                dots_len = avail - len(name) - 1 - len(count_str) - 1
                if dots_len < 1:
                    dots_len = 1
                dots = '.' * dots_len
                text = f' {name} {dots} {count_str}'
                self._safe_addstr(row, col + 3, text, row_attr)

        # Footer
        footer = '[W/S] Scroll  [1-5] Hotbar  [I] Close'
        footer_col = start_col + (box_w - len(footer)) // 2
        self._safe_addstr(start_row + box_h - 2, footer_col, footer, curses.A_DIM)

        self.stdscr.refresh()

    def render_crafting(self,
                        inventory: Inventory,
                        recipes: List[Any],
                        recipe_cursor: int = 0) -> None:
        """Render crafting panel with inventory (left) and recipes (right)."""
        self.stdscr.erase()

        box_w = min(76, self.width - 2)
        box_h = min(24, self.height - 2)
        start_col = (self.width - box_w) // 2
        start_row = (self.height - box_h) // 2

        border_attr = curses.A_BOLD
        top = '+' + '-' * (box_w - 2) + '+'
        self._safe_addstr(start_row, start_col, top, border_attr)
        self._safe_addstr(start_row + box_h - 1, start_col, top, border_attr)
        for r in range(1, box_h - 1):
            line = '|' + ' ' * (box_w - 2) + '|'
            self._safe_addstr(start_row + r, start_col, line, border_attr)

        title = 'CRAFTING'
        title_col = start_col + (box_w - len(title)) // 2
        self._safe_addstr(start_row + 1, title_col, title, curses.A_BOLD)

        inner_left = start_col + 2
        inner_right = start_col + box_w - 3
        inner_top = start_row + 3
        inner_bottom = start_row + box_h - 3

        mid_col = start_col + box_w // 2
        for row in range(inner_top, inner_bottom + 1):
            self._safe_addstr(row, mid_col, '|', curses.A_DIM)

        self._safe_addstr(inner_top - 1, inner_left, 'Inventory', curses.A_BOLD)
        self._safe_addstr(inner_top - 1, mid_col + 2, 'Available Recipes', curses.A_BOLD)

        # Left panel: inventory list
        items = inventory.items()
        left_width = (mid_col - 1) - inner_left
        max_rows = max(1, inner_bottom - inner_top + 1)

        if not items:
            self._safe_addstr(inner_top, inner_left, 'Empty', curses.A_DIM)
        else:
            for i, (item_type, count) in enumerate(items[:max_rows]):
                if isinstance(item_type, BlockType):
                    props = get_properties(item_type)
                    name = display_name(item_type)
                    color_pair = props.color_pair
                    item_char = props.char
                else:
                    props = get_item_properties(item_type)
                    name = item_display_name(item_type)
                    color_pair = 0
                    item_char = props.char

                count_str = f'x {count}'
                dots_len = max(1, left_width - len(name) - len(count_str) - 4)
                text = f' {item_char} {name} {"." * dots_len} {count_str}'
                row = inner_top + i
                attr = curses.A_NORMAL
                if curses.has_colors() and color_pair > 0:
                    attr |= curses.color_pair(color_pair)
                self._safe_addstr(row, inner_left, text[:left_width], attr)

        # Right panel: available recipes list
        right_col = mid_col + 2
        right_width = inner_right - right_col + 1

        if not recipes:
            self._safe_addstr(inner_top, right_col, 'No craftable recipes', curses.A_DIM)
        else:
            clamped_cursor = max(0, min(recipe_cursor, len(recipes) - 1))
            for i, recipe in enumerate(recipes[:max_rows]):
                row = inner_top + i
                marker = '>' if i == clamped_cursor else ' '
                attr = curses.A_REVERSE if i == clamped_cursor else curses.A_NORMAL
                recipe_name = getattr(recipe, 'name', str(recipe))

                outputs = getattr(recipe, 'outputs', ())
                output_preview = ''
                if outputs:
                    first = outputs[0]
                    out_item = getattr(first, 'item', '?')
                    out_count = getattr(first, 'count', 1)
                    output_preview = f' -> {out_count} {out_item.replace("_", " ")}'

                line = f'{marker} {recipe_name}{output_preview}'
                self._safe_addstr(row, right_col, line[:right_width], attr)

        footer = '[W/S] Select Recipe  [Enter/Space] Craft  [C] Close'
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
