"""Lightweight event-driven sound cues for terminal gameplay.

Uses curses.beep() when available, with a terminal bell fallback.
All playback is best-effort and non-fatal.
"""

from __future__ import annotations

import curses
import sys
import time
from enum import Enum


class SoundEvent(str, Enum):
    FOOTSTEP = "footstep"
    MINING = "mining"
    HIT = "hit"
    DEATH = "death"


class SoundManager:
    """Plays simple event-driven sound cues with per-event cooldowns."""

    def __init__(self) -> None:
        self.enabled = True
        now = 0.0
        self._last_played = {event: now for event in SoundEvent}
        self._cooldowns = {
            SoundEvent.FOOTSTEP: 0.08,
            SoundEvent.MINING: 0.05,
            SoundEvent.HIT: 0.15,
            SoundEvent.DEATH: 0.5,
        }

    def play(self, event: SoundEvent) -> None:
        """Play a cue for the given event.

        Best effort only: failures are ignored to avoid disrupting gameplay.
        """
        if not self.enabled:
            return

        now = time.monotonic()
        cooldown = self._cooldowns.get(event, 0.0)
        if now - self._last_played.get(event, 0.0) < cooldown:
            return

        self._last_played[event] = now
        count = 1
        if event == SoundEvent.HIT:
            count = 2
        elif event == SoundEvent.DEATH:
            count = 3

        for _ in range(count):
            try:
                curses.beep()
            except Exception:
                try:
                    sys.stdout.write("\a")
                    sys.stdout.flush()
                except Exception:
                    return
