"""2D Vector class for position and velocity calculations."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple


@dataclass
class Vec2:
    """2D vector with basic math operations."""
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Vec2":
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> "Vec2":
        return Vec2(self.x / scalar, self.y / scalar)

    def __neg__(self) -> "Vec2":
        return Vec2(-self.x, -self.y)

    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)

    def to_int(self) -> tuple[int, int]:
        """Convert to integer tuple for grid coordinates."""
        return (int(self.x), int(self.y))

    def floor(self) -> "Vec2":
        """Return a new Vec2 with floored components."""
        import math
        return Vec2(math.floor(self.x), math.floor(self.y))
