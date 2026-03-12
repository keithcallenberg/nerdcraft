"""Item definitions for non-block inventory items."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class ItemType(Enum):
    """Non-placeable inventory item types."""

    APPLE = auto()
    RAW_MEAT = auto()

    WOOD_PICKAXE = auto()
    STONE_PICKAXE = auto()
    IRON_PICKAXE = auto()

    WOOD_SWORD = auto()
    STONE_SWORD = auto()
    IRON_SWORD = auto()


class ItemClass(Enum):
    """High-level class used by gameplay logic."""

    MATERIAL = auto()
    CONSUMABLE = auto()
    TOOL = auto()
    WEAPON = auto()


@dataclass(frozen=True)
class ItemProperties:
    """Display and behavior metadata for item types."""

    char: str
    item_class: ItemClass = ItemClass.MATERIAL
    heal_amount: int = 0
    mining_tier: int = 0
    attack_damage: int = 0


_ITEM_PROPERTIES: dict[ItemType, ItemProperties] = {
    ItemType.APPLE: ItemProperties(
        char='a', item_class=ItemClass.CONSUMABLE, heal_amount=12
    ),
    ItemType.RAW_MEAT: ItemProperties(
        char='m', item_class=ItemClass.CONSUMABLE, heal_amount=20
    ),

    ItemType.WOOD_PICKAXE: ItemProperties(
        char='T', item_class=ItemClass.TOOL, mining_tier=1
    ),
    ItemType.STONE_PICKAXE: ItemProperties(
        char='T', item_class=ItemClass.TOOL, mining_tier=2
    ),
    ItemType.IRON_PICKAXE: ItemProperties(
        char='T', item_class=ItemClass.TOOL, mining_tier=3
    ),

    ItemType.WOOD_SWORD: ItemProperties(
        char='/', item_class=ItemClass.WEAPON, attack_damage=8
    ),
    ItemType.STONE_SWORD: ItemProperties(
        char='/', item_class=ItemClass.WEAPON, attack_damage=12
    ),
    ItemType.IRON_SWORD: ItemProperties(
        char='/', item_class=ItemClass.WEAPON, attack_damage=16
    ),
}


def get_item_properties(item_type: ItemType) -> ItemProperties:
    """Get properties for a given item type."""

    return _ITEM_PROPERTIES[item_type]


def item_display_name(item_type: ItemType) -> str:
    """Human-friendly item display names."""

    return item_type.name.replace('_', ' ').title()
