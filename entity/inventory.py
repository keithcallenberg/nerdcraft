"""Player inventory for collected blocks."""

from __future__ import annotations

from world.block import BlockType


class Inventory:
    """Stores collected block items with quantities."""

    def __init__(self):
        self._items: dict[BlockType, int] = {}

    def add(self, block_type: BlockType) -> None:
        """Add one block to the inventory."""
        self._items[block_type] = self._items.get(block_type, 0) + 1

    def remove(self, block_type: BlockType) -> bool:
        """Remove one block. Returns True if successful, False if not in inventory."""
        count = self._items.get(block_type, 0)
        if count <= 0:
            return False
        if count == 1:
            del self._items[block_type]
        else:
            self._items[block_type] = count - 1
        return True

    def count(self, block_type: BlockType) -> int:
        """Get count of a specific block type."""
        return self._items.get(block_type, 0)

    def items(self) -> list[tuple[BlockType, int]]:
        """Return list of (BlockType, count) pairs."""
        return list(self._items.items())

    def is_empty(self) -> bool:
        return len(self._items) == 0
