"""Item definitions for non-block inventory items."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class ItemType(Enum):
    """Non-placeable inventory item types."""

    APPLE = auto()
    RAW_MEAT = auto()


@dataclass(frozen=True)
class ItemProperties:
    """Display and behavior metadata for item types."""

    char: str
    consumable: bool = False
    heal_amount: int = 0


_ITEM_PROPERTIES: dict[ItemType, ItemProperties] = {
    ItemType.APPLE: ItemProperties(char='a', consumable=True, heal_amount=12),
    ItemType.RAW_MEAT: ItemProperties(char='m', consumable=True, heal_amount=20),
}


def get_item_properties(item_type: ItemType) -> ItemProperties:
    """Get properties for a given item type."""

    return _ITEM_PROPERTIES[item_type]


def item_display_name(item_type: ItemType) -> str:
    """Human-friendly item display names."""

    return item_type.name.replace('_', ' ').title()
