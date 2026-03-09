"""Day/night clock utilities.

This module tracks simulation ticks and exposes helpers for deriving
in-game time-of-day state.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DayClock:
    """Track world time based on simulation ticks.

    The clock wraps every ``day_length_ticks`` and provides convenience
    accessors used by rendering/HUD and future spawn rules.
    """

    day_length_ticks: int
    total_ticks: int = 0

    def __post_init__(self) -> None:
        if self.day_length_ticks <= 0:
            raise ValueError("day_length_ticks must be > 0")

    def tick(self, ticks: int = 1) -> None:
        """Advance the clock by ``ticks`` simulation steps."""
        if ticks < 0:
            raise ValueError("ticks must be >= 0")
        self.total_ticks += ticks

    @property
    def tick_in_day(self) -> int:
        """Current tick offset within the active day cycle."""
        return self.total_ticks % self.day_length_ticks

    @property
    def day_progress(self) -> float:
        """Normalized day progress in ``[0.0, 1.0)``."""
        return self.tick_in_day / self.day_length_ticks

    @property
    def is_day(self) -> bool:
        """Whether the current time is daytime.

        Current definition is a simple half-cycle split:
        first half of each cycle is day, second half is night.
        """
        return self.tick_in_day < (self.day_length_ticks // 2)

    @property
    def is_night(self) -> bool:
        """Whether the current time is nighttime."""
        return not self.is_day

    @property
    def hud_icon(self) -> str:
        """Time-of-day icon for HUD display."""
        return "☀" if self.is_day else "☾"

    def time_hhmm(self) -> str:
        """Return clock time as a 24h string based on cycle progress."""
        total_minutes = int(self.day_progress * 24 * 60)
        hours = (total_minutes // 60) % 24
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"
