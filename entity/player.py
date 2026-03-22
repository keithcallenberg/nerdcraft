"""Player entity with integer grid position."""

from __future__ import annotations

from config import GameConfig
from entity.inventory import Inventory
from entity.item import ItemType, get_item_properties


class Player:
    """The player entity occupying a single cell."""

    def __init__(self, x: int = 0, y: int = 0):
        """Initialize player at given grid position."""
        self.x = x
        self.y = y
        self.on_ground = False
        self.facing_right = True
        self.jump_remaining = 0  # blocks left to rise
        self.health = GameConfig.get().combat.max_health
        self.fall_distance = 0  # blocks fallen continuously
        self.inventory = Inventory()
        self.armor: dict[str, ItemType | None] = {
            'helmet': None,
            'chestpiece': None,
            'pants': None,
        }

    def get_block_in_direction(self, direction: str) -> tuple[int, int]:
        """Get the adjacent block position for a direction."""
        if direction == 'left':
            return (self.x - 1, self.y)
        elif direction == 'right':
            return (self.x + 1, self.y)
        elif direction == 'up':
            return (self.x, self.y + 1)
        else:  # down
            return (self.x, self.y - 1)

    def get_minable_positions_in_direction(self, direction: str) -> list[tuple[int, int]]:
        """Get mineable positions for a direction, in priority order."""
        if direction == 'left':
            return [(self.x - 1, self.y)]
        elif direction == 'right':
            return [(self.x + 1, self.y)]
        elif direction == 'up':
            return [(self.x, self.y + 1)]
        else:  # down
            return [(self.x, self.y - 1)]

    def equip_armor(self, item_type: ItemType) -> bool:
        """Equip an armor item from inventory. Returns True if equipped."""
        props = get_item_properties(item_type)
        slot = props.armor_slot.strip().lower()
        if slot not in self.armor:
            return False
        if not self.inventory.remove(item_type):
            return False

        current = self.armor.get(slot)
        if current is not None:
            self.inventory.add(current)
        self.armor[slot] = item_type
        return True

    def total_armor_defense(self) -> int:
        total = 0
        for item in self.armor.values():
            if item is None:
                continue
            total += max(0, get_item_properties(item).armor_defense)
        return total
