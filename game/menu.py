"""Main menu UI for world selection and creation."""

from __future__ import annotations

import curses
from dataclasses import dataclass
from pathlib import Path

from config import GameConfig, _load_json


@dataclass
class MenuResult:
    start_game: bool
    save_name: str = "default"
    force_new: bool = False
    seed: int | None = None


class MainMenu:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.cfg = GameConfig.get()
        self._menu_cfg = self._load_menu_config()

    def _load_menu_config(self) -> dict:
        try:
            return _load_json("menu.json")
        except Exception:
            return {}

    def _header_lines(self) -> list[str]:
        lines = self._menu_cfg.get("header_lines")
        if isinstance(lines, list) and lines:
            return [str(x) for x in lines]
        return ["NERDCRAFT"]

    def _labels(self) -> tuple[str, str, str]:
        menu_cfg = self._menu_cfg.get("menu", {}) if isinstance(self._menu_cfg, dict) else {}
        return (
            str(menu_cfg.get("new_world_label", "Generate New World")),
            str(menu_cfg.get("load_world_label", "Load Saved World")),
            str(menu_cfg.get("quit_label", "Quit")),
        )

    def _list_saves(self) -> list[str]:
        root = self.cfg.save.save_dir
        if not root.exists():
            return []
        saves: list[str] = []
        for p in sorted(root.iterdir()):
            if not p.is_dir():
                continue
            if (p / "meta.json").exists() and (p / "world.pkl").exists() and (p / "player.json").exists():
                saves.append(p.name)
        return saves

    def run(self) -> MenuResult:
        curses.curs_set(0)
        self.stdscr.nodelay(False)
        self.stdscr.keypad(True)

        new_label, load_label, quit_label = self._labels()
        options = [new_label, load_label, quit_label]
        idx = 0

        while True:
            self.stdscr.erase()
            h, w = self.stdscr.getmaxyx()

            # Header
            y = 1
            for line in self._header_lines():
                x = max(0, (w - len(line)) // 2)
                try:
                    self.stdscr.addstr(y, x, line, curses.A_BOLD)
                except curses.error:
                    pass
                y += 1

            y += 1
            for i, label in enumerate(options):
                x = max(0, (w - len(label) - 4) // 2)
                prefix = "> " if i == idx else "  "
                attr = curses.A_REVERSE if i == idx else curses.A_NORMAL
                try:
                    self.stdscr.addstr(y + i, x, f"{prefix}{label}", attr)
                except curses.error:
                    pass

            hint = "W/S or ↑/↓ to select, Enter to confirm"
            try:
                self.stdscr.addstr(h - 2, max(0, (w - len(hint)) // 2), hint, curses.A_DIM)
            except curses.error:
                pass

            self.stdscr.refresh()

            k = self.stdscr.getch()
            if k in (ord('w'), ord('W'), curses.KEY_UP):
                idx = (idx - 1) % len(options)
            elif k in (ord('s'), ord('S'), curses.KEY_DOWN):
                idx = (idx + 1) % len(options)
            elif k in (10, 13, curses.KEY_ENTER):
                if idx == 0:
                    return self._new_world_flow()
                if idx == 1:
                    return self._load_world_flow()
                return MenuResult(start_game=False)
            elif k in (ord('q'), ord('Q'), 27):
                return MenuResult(start_game=False)

    def _prompt_text(self, prompt: str, default: str = "") -> str:
        curses.echo()
        curses.curs_set(1)
        self.stdscr.erase()
        h, _ = self.stdscr.getmaxyx()
        try:
            self.stdscr.addstr(h // 2 - 1, 2, prompt)
            self.stdscr.addstr(h // 2, 2, f"> {default}")
            self.stdscr.move(h // 2, 4 + len(default))
        except curses.error:
            pass
        self.stdscr.refresh()
        s = self.stdscr.getstr(h // 2, 4 + len(default), 64)
        curses.noecho()
        curses.curs_set(0)
        text = s.decode("utf-8", errors="ignore").strip()
        return text or default

    def _new_world_flow(self) -> MenuResult:
        """Single-screen new world setup with editable settings."""
        sizes: list[tuple[str, tuple[int, int]]] = [
            ("Small", (40, 12)),
            ("Medium", (64, 16)),
            ("Large", (96, 24)),
        ]

        save_name = "default"
        seed_text = ""
        size_index = 1
        field_index = 0

        while True:
            self.stdscr.erase()
            h, w = self.stdscr.getmaxyx()
            title = "Create New World"
            try:
                self.stdscr.addstr(1, max(0, (w - len(title)) // 2), title, curses.A_BOLD)
            except curses.error:
                pass

            fields = [
                ("Save Name", save_name or "default"),
                ("Seed", seed_text or "(random)"),
                ("World Size", f"{sizes[size_index][0]} ({sizes[size_index][1][0]}x{sizes[size_index][1][1]} chunks)"),
                ("Generate", "Press Enter"),
            ]

            start_y = 4
            for i, (label, value) in enumerate(fields):
                line = f"{label}: {value}"
                attr = curses.A_REVERSE if i == field_index else curses.A_NORMAL
                try:
                    self.stdscr.addstr(start_y + i * 2, max(2, (w - len(line)) // 2), line, attr)
                except curses.error:
                    pass

            hint = "W/S: field  A/D: change size  Enter: edit/confirm  Esc: back"
            try:
                self.stdscr.addstr(h - 2, max(0, (w - len(hint)) // 2), hint, curses.A_DIM)
            except curses.error:
                pass
            self.stdscr.refresh()

            k = self.stdscr.getch()
            if k in (ord('w'), ord('W'), curses.KEY_UP):
                field_index = (field_index - 1) % len(fields)
            elif k in (ord('s'), ord('S'), curses.KEY_DOWN):
                field_index = (field_index + 1) % len(fields)
            elif k in (ord('a'), ord('A'), curses.KEY_LEFT) and field_index == 2:
                size_index = (size_index - 1) % len(sizes)
            elif k in (ord('d'), ord('D'), curses.KEY_RIGHT) and field_index == 2:
                size_index = (size_index + 1) % len(sizes)
            elif k in (10, 13, curses.KEY_ENTER):
                if field_index == 0:
                    save_name = self._prompt_text("Enter world/save name:", save_name or "default")
                elif field_index == 1:
                    seed_text = self._prompt_text("Seed (blank = random):", seed_text)
                elif field_index == 2:
                    size_index = (size_index + 1) % len(sizes)
                elif field_index == 3:
                    seed: int | None = None
                    if seed_text.strip():
                        try:
                            seed = int(seed_text.strip())
                        except ValueError:
                            seed = None
                    return MenuResult(
                        start_game=True,
                        save_name=save_name or "default",
                        force_new=True,
                        seed=seed,
                        world_size_chunks=sizes[size_index][1],
                    )
            elif k in (27, ord('q'), ord('Q')):
                return self.run()

    def _load_world_flow(self) -> MenuResult:
        saves = self._list_saves()
        if not saves:
            self.stdscr.erase()
            msg = "No saved worlds found. Press any key..."
            h, w = self.stdscr.getmaxyx()
            try:
                self.stdscr.addstr(h // 2, max(0, (w - len(msg)) // 2), msg)
            except curses.error:
                pass
            self.stdscr.refresh()
            self.stdscr.getch()
            return self.run()

        idx = 0
        while True:
            self.stdscr.erase()
            h, w = self.stdscr.getmaxyx()
            title = "Load Saved World"
            try:
                self.stdscr.addstr(1, max(0, (w - len(title)) // 2), title, curses.A_BOLD)
            except curses.error:
                pass

            for i, name in enumerate(saves):
                x = max(0, (w - len(name) - 4) // 2)
                prefix = "> " if i == idx else "  "
                attr = curses.A_REVERSE if i == idx else curses.A_NORMAL
                try:
                    self.stdscr.addstr(3 + i, x, f"{prefix}{name}", attr)
                except curses.error:
                    pass

            self.stdscr.refresh()
            k = self.stdscr.getch()
            if k in (ord('w'), ord('W'), curses.KEY_UP):
                idx = (idx - 1) % len(saves)
            elif k in (ord('s'), ord('S'), curses.KEY_DOWN):
                idx = (idx + 1) % len(saves)
            elif k in (10, 13, curses.KEY_ENTER):
                return MenuResult(start_game=True, save_name=saves[idx], force_new=False, seed=None)
            elif k in (ord('q'), ord('Q'), 27):
                return self.run()
