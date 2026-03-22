"""Save and load game state to/from disk."""

from __future__ import annotations

import json
import pickle
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from world.world import World
    from entity.player import Player

# Save format version — bump if layout changes incompatibly
SAVE_VERSION = 1


class SaveManager:
    """Handles serialization and deserialization of game state.

    Save layout::

        saves/<name>/
            meta.json    – seed, version, timestamp
            world.pkl    – chunk block arrays (fast binary)
            player.json  – player state (human-readable)
    """

    def __init__(self, save_dir: str | Path, save_name: str = "default"):
        root = Path(save_dir)
        self.save_path = root / save_name
        self._save_name = save_name

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_exists(self) -> bool:
        """Return True if a complete save is present."""
        return (
            (self.save_path / "meta.json").exists()
            and (self.save_path / "world.pkl").exists()
            and (self.save_path / "player.json").exists()
        )

    def save(self, world: "World", player: "Player", seed: int) -> None:
        """Write world + player state to disk."""
        self.save_path.mkdir(parents=True, exist_ok=True)
        self._write_meta(seed)
        self._write_world(world)
        self._write_player(player)

    def load(self, world: "World", player: "Player") -> int:
        """Load world + player state from disk into existing objects.

        Returns the original generation seed so the engine can recreate
        a WorldGenerator for spawn-position queries etc.
        """
        meta = self._read_meta()
        self._read_world(world)
        self._read_player(player)
        return meta["seed"]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_meta(self, seed: int) -> None:
        meta = {
            "version": SAVE_VERSION,
            "seed": seed,
            "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "save_name": self._save_name,
        }
        with open(self.save_path / "meta.json", "w") as f:
            json.dump(meta, f, indent=2)

    def _read_meta(self) -> dict[str, Any]:
        with open(self.save_path / "meta.json") as f:
            return json.load(f)

    def _write_world(self, world: "World") -> None:
        """Pickle the raw block data from every loaded chunk."""
        from world.block import BlockType

        chunk_data: dict[tuple[int, int], list[list[int]]] = {}
        for (cx, cy), chunk in world._chunks.items():
            # Store as int values to keep pickle lean
            chunk_data[(cx, cy)] = [
                [b.value for b in col]
                for col in chunk._blocks
            ]

        with open(self.save_path / "world.pkl", "wb") as f:
            pickle.dump(chunk_data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def _read_world(self, world: "World") -> None:
        """Restore chunk block data into the world object."""
        from world.block import BlockType
        from world.chunk import Chunk

        # Build reverse map: int value → BlockType
        _val_to_block = {b.value: b for b in BlockType}

        with open(self.save_path / "world.pkl", "rb") as f:
            chunk_data: dict = pickle.load(f)

        world._chunks.clear()
        for (cx, cy), raw_cols in chunk_data.items():
            chunk = Chunk(cx, cy)
            for lx, col in enumerate(raw_cols):
                for ly, val in enumerate(col):
                    chunk._blocks[lx][ly] = _val_to_block.get(val, BlockType.AIR)
            world._chunks[(cx, cy)] = chunk

    def _write_player(self, player: "Player") -> None:
        """Write player state as human-readable JSON."""
        from entity.item import ItemType
        from world.block import BlockType

        def _inv_key(item: BlockType | ItemType) -> str:
            if isinstance(item, BlockType):
                return f"block:{item.name}"
            return f"item:{item.name}"

        state = {
            "x": player.x,
            "y": player.y,
            "health": player.health,
            "facing_right": player.facing_right,
            "inventory": {
                _inv_key(item): count
                for item, count in player.inventory.items()
            },
            "armor": {
                slot: (item.name if item is not None else None)
                for slot, item in player.armor.items()
            },
        }
        with open(self.save_path / "player.json", "w") as f:
            json.dump(state, f, indent=2)

    def _read_player(self, player: "Player") -> None:
        """Restore player state from JSON."""
        from entity.item import ItemType
        from world.block import BlockType

        with open(self.save_path / "player.json") as f:
            state = json.load(f)

        player.x = state["x"]
        player.y = state["y"]
        player.health = state["health"]
        player.facing_right = state.get("facing_right", True)
        player.on_ground = False
        player.jump_remaining = 0
        player.fall_distance = 0

        player.inventory._items.clear()
        _name_to_block = {b.name: b for b in BlockType}
        _name_to_item = {i.name: i for i in ItemType}

        for raw_name, count in state.get("inventory", {}).items():
            if count <= 0:
                continue

            if ":" in raw_name:
                prefix, name = raw_name.split(":", 1)
                if prefix == "block":
                    # Leather migrated from block -> item
                    if name == "LEATHER":
                        item = _name_to_item.get("LEATHER")
                        if item is not None:
                            player.inventory._items[item] = count
                            continue
                    block = _name_to_block.get(name)
                    if block is not None:
                        player.inventory._items[block] = count
                elif prefix == "item":
                    item = _name_to_item.get(name)
                    if item is not None:
                        player.inventory._items[item] = count
                continue

            # Backward compatibility with old save format
            item = _name_to_item.get(raw_name)
            if item is not None:
                player.inventory._items[item] = count
                continue

            block = _name_to_block.get(raw_name)
            if block is not None:
                if raw_name == "LEATHER":
                    item = _name_to_item.get("LEATHER")
                    if item is not None:
                        player.inventory._items[item] = count
                else:
                    player.inventory._items[block] = count

        player.armor = {'helmet': None, 'chestpiece': None, 'pants': None}
        for slot, raw_item in state.get("armor", {}).items():
            if slot not in player.armor or not raw_item:
                continue
            item = _name_to_item.get(str(raw_item))
            if item is not None:
                player.armor[slot] = item
