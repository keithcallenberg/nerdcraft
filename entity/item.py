"""Item definitions loaded dynamically from config/items.json."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from config import GameConfig, _load_json
from world.block import _RegistryValue


_ITEM_INSTANCES: dict[str, "ItemType"] = {}
_ITEM_MEMBER_CACHE: dict[str, "ItemType"] = {}
_ITEM_ID_CACHE: tuple[str, ...] = ()


class _ItemTypeMeta(type):
    """Metaclass exposing JSON-defined items through enum-like access."""

    def _item_ids(cls) -> tuple[str, ...]:
        global _ITEM_ID_CACHE
        if not _ITEM_ID_CACHE:
            data = _load_json("items.json")
            _ITEM_ID_CACHE = tuple(data.get("items", {}).keys())
        return _ITEM_ID_CACHE

    def _get_instance(cls, item_id: str) -> ItemType:
        normalized = str(item_id).strip().lower()
        instance = _ITEM_INSTANCES.get(normalized)
        if instance is None:
            instance = super().__call__(normalized)
            _ITEM_INSTANCES[normalized] = instance
            type.__setattr__(cls, normalized.upper(), instance)
        return instance

    @property
    def __members__(cls) -> dict[str, ItemType]:
        global _ITEM_MEMBER_CACHE
        if not _ITEM_MEMBER_CACHE:
            _ITEM_MEMBER_CACHE = {
                item_id.upper(): cls._get_instance(item_id)
                for item_id in cls._item_ids()
            }
        return _ITEM_MEMBER_CACHE

    def __iter__(cls):
        return iter(cls.__members__.values())

    def __getitem__(cls, key: str) -> ItemType:
        item_id = str(key).strip().lower()
        if item_id not in cls._item_ids():
            raise KeyError(key)
        return cls._get_instance(item_id)

    def __getattr__(cls, name: str) -> ItemType:
        try:
            return cls[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __contains__(cls, key: object) -> bool:
        if isinstance(key, ItemType):
            return key.content_id in cls._item_ids()
        if isinstance(key, str):
            return key.strip().lower() in cls._item_ids()
        return False


class ItemType(_RegistryValue, metaclass=_ItemTypeMeta):
    """JSON-defined item identifier."""


class ItemClass(Enum):
    """High-level class used by gameplay logic."""

    MATERIAL = auto()
    CONSUMABLE = auto()
    TOOL = auto()
    WEAPON = auto()
    ARMOR = auto()


@dataclass(frozen=True)
class ItemProperties:
    """Display and behavior metadata for item types."""

    char: str
    color_pair: int = 0
    item_class: ItemClass = ItemClass.MATERIAL
    heal_amount: int = 0
    mining_tier: int = 0
    attack_damage: int = 0
    range: int = 1
    armor_slot: str = ""
    armor_defense: int = 0


_ITEM_PROPERTIES: dict[ItemType, ItemProperties] = {}
_INITIALIZED = False


def item_exists(item_id: str) -> bool:
    """Return True when an item id exists in JSON configuration."""
    return item_id.strip().lower() in ItemType


def _json_name(item_type: ItemType) -> str:
    return item_type.value


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
    if text == "armor":
        return ItemClass.ARMOR
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
            range=max(1, int(item_cfg.get("range", 1))),
            armor_slot=str(item_cfg.get("armor_slot", "")),
            armor_defense=int(item_cfg.get("armor_defense", 0)),
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
    global _INITIALIZED, _ITEM_ID_CACHE, _ITEM_MEMBER_CACHE

    _INITIALIZED = False
    _ITEM_ID_CACHE = ()
    _ITEM_MEMBER_CACHE = {}
    for key in list(_ITEM_INSTANCES):
        name = key.upper()
        if hasattr(ItemType, name):
            type.__delattr__(ItemType, name)
    _ITEM_INSTANCES.clear()
    GameConfig.reload()
    _init_from_config()
