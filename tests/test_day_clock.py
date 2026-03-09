"""Tests for day/night clock behavior."""

from __future__ import annotations

import unittest

from game.clock import DayClock


class DayClockTests(unittest.TestCase):
    def test_wraps_tick_in_day(self) -> None:
        clock = DayClock(day_length_ticks=10)
        clock.tick(12)
        self.assertEqual(clock.tick_in_day, 2)

    def test_is_day_and_night_split_half_cycle(self) -> None:
        clock = DayClock(day_length_ticks=10)

        clock.tick(4)
        self.assertTrue(clock.is_day)
        self.assertFalse(clock.is_night)

        clock.tick(1)
        self.assertFalse(clock.is_day)
        self.assertTrue(clock.is_night)

    def test_hud_icon_matches_time_of_day(self) -> None:
        clock = DayClock(day_length_ticks=8)
        self.assertEqual(clock.hud_icon, "☀")
        clock.tick(4)
        self.assertEqual(clock.hud_icon, "☾")

    def test_time_hhmm_maps_progress(self) -> None:
        clock = DayClock(day_length_ticks=240)
        self.assertEqual(clock.time_hhmm(), "00:00")

        clock.tick(60)  # 25% through day
        self.assertEqual(clock.time_hhmm(), "06:00")

    def test_invalid_inputs_raise(self) -> None:
        with self.assertRaises(ValueError):
            DayClock(day_length_ticks=0)

        clock = DayClock(day_length_ticks=10)
        with self.assertRaises(ValueError):
            clock.tick(-1)


if __name__ == "__main__":
    unittest.main()
