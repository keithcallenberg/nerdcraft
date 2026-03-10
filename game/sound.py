"""Lightweight event-driven sound cues for terminal gameplay.

Uses curses.beep() when available, with a terminal bell fallback.
All playback is best-effort and non-fatal.
"""

from __future__ import annotations

import curses
import sys
import time
from enum import Enum

from config import GameConfig


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
        self._beep_counts = {
            SoundEvent.FOOTSTEP: 1,
            SoundEvent.MINING: 1,
            SoundEvent.HIT: 2,
            SoundEvent.DEATH: 3,
        }
        self._event_enabled = {event: True for event in SoundEvent}

        # Optional JSON overrides from config/sounds.json
        try:
            cfg = GameConfig.get()
            for event in SoundEvent:
                event_cfg = cfg.sounds.get(event.value)
                if event_cfg is None:
                    continue
                self._event_enabled[event] = event_cfg.enabled
                self._cooldowns[event] = event_cfg.cooldown
                self._beep_counts[event] = event_cfg.beep_count
        except Exception:
            # Never fail game startup due to audio config issues.
            pass

    def play(self, event: SoundEvent) -> None:
        """Play a cue for the given event.

        Best effort only: failures are ignored to avoid disrupting gameplay.
        """
        if not self.enabled:
            return

        if not self._event_enabled.get(event, True):
            return

        now = time.monotonic()
        cooldown = self._cooldowns.get(event, 0.0)
        if now - self._last_played.get(event, 0.0) < cooldown:
            return

        self._last_played[event] = now
        count = self._beep_counts.get(event, 1)

        for _ in range(count):
            try:
                curses.beep()
            except Exception:
                try:
                    sys.stdout.write("\a")
                    sys.stdout.flush()
                except Exception:
                    return
