"""Registry of mob definitions loaded from config/mobs.json."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DropDef:
    item: str        # BlockType name (uppercase)
    chance: float    # 0.0 – 1.0
    count: int


@dataclass
class SpawnDef:
    surface: bool
    underground: bool
    night_only: bool
    weight: int      # relative spawn weight


@dataclass
class MobDef:
    mob_id: str
    name: str
    char: str
    color: str
    health: int
    hostile: bool
    detection_range: int   # blocks — hostile mobs chase within this range
    attack_damage: int
    attack_interval: float # seconds between attacks
    move_interval: float   # seconds between movement steps (chase/active)
    idle_move_interval: float  # seconds between passive wander steps
    move_speed: int  # blocks moved per movement action
    drops: list[DropDef]
    spawn: SpawnDef


class MobRegistry:
    """Singleton registry of mob definitions loaded from JSON."""

    _instance: MobRegistry | None = None

    def __init__(self):
        self._defs: dict[str, MobDef] = {}
        self._load()

    @classmethod
    def get(cls) -> MobRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reload(cls) -> MobRegistry:
        cls._instance = cls()
        return cls._instance

    def _load(self) -> None:
        config_path = Path(__file__).parent.parent / "config" / "mobs.json"
        with open(config_path) as f:
            data = json.load(f)

        for mob_id, props in data.get("mobs", {}).items():
            drops = [
                DropDef(
                    item=d["item"],
                    chance=d.get("chance", 1.0),
                    count=d.get("count", 1),
                )
                for d in props.get("drops", [])
            ]
            spawn_raw = props.get("spawn", {})
            spawn = SpawnDef(
                surface=spawn_raw.get("surface", True),
                underground=spawn_raw.get("underground", False),
                night_only=spawn_raw.get("night_only", False),
                weight=spawn_raw.get("weight", 10),
            )
            self._defs[mob_id] = MobDef(
                mob_id=mob_id,
                name=props.get("name", mob_id),
                char=props.get("char", "?"),
                color=props.get("color", "white"),
                health=props.get("health", 10),
                hostile=props.get("hostile", False),
                detection_range=props.get("detection_range", 0),
                attack_damage=props.get("attack_damage", 0),
                attack_interval=props.get("attack_interval", 1.0),
                move_interval=props.get("move_interval", 1.5),
                idle_move_interval=props.get(
                    "idle_move_interval",
                    float(props.get("move_interval", 1.5)) * 1.8,
                ),
                move_speed=max(1, int(props.get("move_speed", 1))),
                drops=drops,
                spawn=spawn,
            )

    def get_def(self, mob_id: str) -> MobDef | None:
        return self._defs.get(mob_id)

    def all_defs(self) -> list[MobDef]:
        return list(self._defs.values())

    def surface_mobs(self) -> list[MobDef]:
        return [d for d in self._defs.values() if d.spawn.surface and not d.spawn.night_only]

    def underground_mobs(self) -> list[MobDef]:
        return [d for d in self._defs.values() if d.spawn.underground]
