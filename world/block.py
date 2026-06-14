"""Block types and properties loaded dynamically from JSON configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


class _RegistryValue:
    """Immutable registry-backed value object."""

    __slots__ = ("content_id", "_hash")

    def __init__(self, content_id: str):
        self.content_id = str(content_id).strip().lower()
        self._hash = hash((type(self), self.content_id))

    @property
    def name(self) -> str:
        return self.content_id.upper()

    @property
    def value(self) -> str:
        return self.content_id

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other) and getattr(other, "content_id", None) == self.content_id

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.content_id!r})"

    def __str__(self) -> str:
        return self.content_id


_BLOCK_INSTANCES: dict[str, "BlockType"] = {}
_BLOCK_MEMBER_CACHE: dict[str, "BlockType"] = {}
_BLOCK_ID_CACHE: tuple[str, ...] = ()


class _BlockTypeMeta(type):
    """Metaclass exposing JSON-defined blocks through enum-like access."""

    def _block_ids(cls) -> tuple[str, ...]:
        from config import GameConfig

        global _BLOCK_ID_CACHE
        if not _BLOCK_ID_CACHE:
            _BLOCK_ID_CACHE = tuple(GameConfig.get().blocks.keys())
        return _BLOCK_ID_CACHE

    def _get_instance(cls, block_id: str) -> BlockType:
        normalized = str(block_id).strip().lower()
        instance = _BLOCK_INSTANCES.get(normalized)
        if instance is None:
            instance = super().__call__(normalized)
            _BLOCK_INSTANCES[normalized] = instance
            type.__setattr__(cls, normalized.upper(), instance)
        return instance

    @property
    def __members__(cls) -> dict[str, BlockType]:
        global _BLOCK_MEMBER_CACHE
        if not _BLOCK_MEMBER_CACHE:
            _BLOCK_MEMBER_CACHE = {
                block_id.upper(): cls._get_instance(block_id)
                for block_id in cls._block_ids()
            }
        return _BLOCK_MEMBER_CACHE

    def __iter__(cls):
        return iter(cls.__members__.values())

    def __getitem__(cls, key: str) -> BlockType:
        block_id = str(key).strip().lower()
        if block_id not in cls._block_ids():
            raise KeyError(key)
        return cls._get_instance(block_id)

    def __getattr__(cls, name: str) -> BlockType:
        try:
            return cls[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __contains__(cls, key: object) -> bool:
        if isinstance(key, BlockType):
            return key.content_id in cls._block_ids()
        if isinstance(key, str):
            return key.strip().lower() in cls._block_ids()
        return False


class BlockType(_RegistryValue, metaclass=_BlockTypeMeta):
    """JSON-defined block identifier."""


@dataclass(frozen=True)
class BlockProperties:
    """Properties for a block type."""

    char: str
    solid: bool = True
    breakable: bool = True
    color_pair: int = 0
    light_radius: int = 0


_block_properties: Dict[BlockType, BlockProperties] = {}
_initialized = False


def block_exists(block_id: str) -> bool:
    """Return True when a block id exists in JSON configuration."""
    return block_id.strip().lower() in BlockType


def _get_json_name(block_type: BlockType) -> str:
    return block_type.value


def _init_from_config() -> None:
    """Initialize block properties from JSON configuration."""
    global _block_properties, _initialized

    if _initialized:
        return

    from config import GameConfig

    cfg = GameConfig.get()
    _block_properties.clear()

    for block_type in BlockType:
        json_name = _get_json_name(block_type)
        block_cfg = cfg.get_block(json_name)

        if block_cfg:
            color_pair = cfg.get_block_color_pair(json_name)
            _block_properties[block_type] = BlockProperties(
                char=block_cfg.char,
                solid=block_cfg.solid,
                breakable=block_cfg.breakable,
                color_pair=color_pair,
                light_radius=block_cfg.light_radius,
            )
        else:
            _block_properties[block_type] = BlockProperties(
                char='?',
                solid=True,
                breakable=True,
                color_pair=0,
            )

    _initialized = True


def get_properties(block_type: BlockType) -> BlockProperties:
    """Get properties for a block type."""
    _init_from_config()
    return _block_properties[block_type]


def is_solid(block_type: BlockType) -> bool:
    """Check if a block type is solid (collidable)."""
    _init_from_config()
    return _block_properties[block_type].solid


def display_name(block_type: BlockType) -> str:
    """Get a human-readable display name for a block type."""
    return block_type.name.replace('_', ' ').title()


def reload_config() -> None:
    """Reload block properties from JSON configuration."""
    global _initialized, _BLOCK_ID_CACHE, _BLOCK_MEMBER_CACHE

    _initialized = False
    _BLOCK_ID_CACHE = ()
    _BLOCK_MEMBER_CACHE = {}
    for key in list(_BLOCK_INSTANCES):
        name = key.upper()
        if hasattr(BlockType, name):
            type.__delattr__(BlockType, name)
    _BLOCK_INSTANCES.clear()
    from config import GameConfig

    GameConfig.reload()
    _init_from_config()
