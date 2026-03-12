"""Player inventory for collected blocks and items."""

from __future__ import annotations

from typing import TypeAlias

from entity.item import ItemType
from world.block import BlockType

InventoryType: TypeAlias = BlockType | ItemType


class Inventory:
    """Stores collected item stacks with quantities."""

    def __init__(self):
        self._items: dict[InventoryType, int] = {}

    def add(self, item_type: InventoryType) -> None:
        """Add one item to the inventory."""
        self._items[item_type] = self._items.get(item_type, 0) + 1

    def remove(self, item_type: InventoryType) -> bool:
        """Remove one item. Returns True if successful, False if not in inventory."""
        count = self._items.get(item_type, 0)
        if count <= 0:
            return False
        if count == 1:
            del self._items[item_type]
        else:
            self._items[item_type] = count - 1
        return True

    def count(self, item_type: InventoryType) -> int:
        """Get count of a specific item type."""
        return self._items.get(item_type, 0)

    def items(self) -> list[tuple[InventoryType, int]]:
        """Return list of (item_type, count) pairs."""
        return list(self._items.items())

    def is_empty(self) -> bool:
        return len(self._items) == 0
