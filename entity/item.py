"""Item definitions for non-block inventory items (JSON-config driven)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from config import GameConfig, _load_json


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
    color_pair: int = 0
    item_class: ItemClass = ItemClass.MATERIAL
    heal_amount: int = 0
    mining_tier: int = 0
    attack_damage: int = 0


_ITEM_PROPERTIES: dict[ItemType, ItemProperties] = {}
_INITIALIZED = False


def _json_name(item_type: ItemType) -> str:
    return item_type.name.lower()


def _parse_item_class(raw: str | None) -> ItemClass:
    if not raw:
        return ItemClass.MATERIAL
    text = raw.strip().lower()
    if text == "consumable":
        return ItemClass.CONSUMABLE
    if text == "tool":
        return ItemClass.TOOL
    if text == "weapon":
        return ItemClass.WEAPON
    return ItemClass.MATERIAL


def _init_from_config() -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return

    cfg = GameConfig.get()
    data = _load_json("items.json")
    raw_items = data.get("items", {})

    _ITEM_PROPERTIES.clear()

    for item_type in ItemType:
        key = _json_name(item_type)
        item_cfg = raw_items.get(key, {})

        color_name = item_cfg.get("color", "default")
        color_pair = cfg.get_color(color_name).pair_id if color_name else 0

        _ITEM_PROPERTIES[item_type] = ItemProperties(
            char=item_cfg.get("char", "?"),
            color_pair=color_pair,
            item_class=_parse_item_class(item_cfg.get("item_class")),
            heal_amount=int(item_cfg.get("heal_amount", 0)),
            mining_tier=int(item_cfg.get("mining_tier", 0)),
            attack_damage=int(item_cfg.get("attack_damage", 0)),
        )

    _INITIALIZED = True


def get_item_properties(item_type: ItemType) -> ItemProperties:
    """Get properties for a given item type."""

    _init_from_config()
    return _ITEM_PROPERTIES[item_type]


def item_display_name(item_type: ItemType) -> str:
    """Human-friendly item display names."""

    return item_type.name.replace('_', ' ').title()


def reload_items_config() -> None:
    """Reload item properties from JSON configuration."""

    global _INITIALIZED
    _INITIALIZED = False
    GameConfig.reload()
    _init_from_config()
