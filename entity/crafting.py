"""Crafting recipe engine backed by config/recipes.json."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Callable

from config import _load_json
from entity.inventory import Inventory, InventoryType
from entity.item import ItemType
from world.block import BlockType


@dataclass(frozen=True)
class RecipeItem:
    """Single input or output stack in a recipe."""

    item: str
    count: int


@dataclass(frozen=True)
class Recipe:
    """Crafting recipe loaded from JSON content."""

    recipe_id: str
    name: str
    inputs: tuple[RecipeItem, ...]
    outputs: tuple[RecipeItem, ...]
    stations: tuple[str, ...]
    description: str


class RecipeEngine:
    """Determines craftable recipes and applies crafting mutations."""

    def __init__(self):
        self._recipes = self._load_recipes()

    def _load_recipes(self) -> dict[str, Recipe]:
        data = _load_json("recipes.json")
        recipes: dict[str, Recipe] = {}

        for raw_recipe in data.get("recipes", []):
            recipe_id = raw_recipe["id"]
            recipes[recipe_id] = Recipe(
                recipe_id=recipe_id,
                name=raw_recipe.get("name", recipe_id),
                inputs=tuple(self._parse_recipe_items(raw_recipe.get("inputs", []))),
                outputs=tuple(self._parse_recipe_items(raw_recipe.get("outputs", []))),
                stations=self._parse_stations(raw_recipe.get("station")),
                description=raw_recipe.get("description", ""),
            )

        return recipes

    def _parse_recipe_items(self, items: list[dict]) -> list[RecipeItem]:
        parsed: list[RecipeItem] = []
        for entry in items:
            parsed.append(
                RecipeItem(
                    item=entry["item"],
                    count=int(entry.get("count", 1)),
                )
            )
        return parsed

    def _parse_stations(self, raw_station) -> tuple[str, ...]:
        """Support station as null, string, plus-delimited string, or array."""
        if raw_station is None:
            return ()
        if isinstance(raw_station, str):
            parts = [s.strip() for s in raw_station.split('+') if s.strip()]
            return tuple(parts)
        if isinstance(raw_station, list):
            return tuple(str(s).strip() for s in raw_station if str(s).strip())
        return ()

    def _to_inventory_type(self, item_name: str) -> InventoryType:
        upper = item_name.upper()
        if upper in ItemType.__members__:
            return ItemType[upper]
        if upper in BlockType.__members__:
            return BlockType[upper]
        raise ValueError(f"Unknown recipe item type: {item_name}")

    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        """Get a recipe by ID."""
        return self._recipes.get(recipe_id)

    def all_recipes(self) -> list[Recipe]:
        """Return all known recipes in load order."""
        return list(self._recipes.values())

    def available_recipes(
        self,
        inventory: Inventory,
        has_station_near: Optional[Callable[[str], bool]] = None,
    ) -> list[Recipe]:
        """Return recipes that can currently be crafted from inventory/context."""
        return [
            recipe
            for recipe in self._recipes.values()
            if self._can_craft(inventory, recipe, has_station_near=has_station_near)
        ]

    def craft(
        self,
        inventory: Inventory,
        recipe_id: str,
        has_station_near: Optional[Callable[[str], bool]] = None,
    ) -> bool:
        """Craft a recipe by ID, mutating inventory. Returns True on success."""
        recipe = self._recipes.get(recipe_id)
        if recipe is None:
            return False

        if not self._can_craft(inventory, recipe, has_station_near=has_station_near):
            return False

        # Consume inputs.
        for req in recipe.inputs:
            item_type = self._to_inventory_type(req.item)
            for _ in range(req.count):
                inventory.remove(item_type)

        # Produce outputs.
        for out in recipe.outputs:
            item_type = self._to_inventory_type(out.item)
            for _ in range(out.count):
                inventory.add(item_type)

        return True

    def _can_craft(
        self,
        inventory: Inventory,
        recipe: Recipe,
        has_station_near: Optional[Callable[[str], bool]] = None,
    ) -> bool:
        # Station requirements are proximity-based when callback is provided.
        if recipe.stations:
            if has_station_near is not None:
                for station_name in recipe.stations:
                    if not has_station_near(station_name):
                        return False
            else:
                # Backward compatibility fallback: require stations in inventory.
                for station_name in recipe.stations:
                    try:
                        station_item = self._to_inventory_type(station_name)
                    except ValueError:
                        return False
                    if inventory.count(station_item) <= 0:
                        return False

        for req in recipe.inputs:
            try:
                req_item = self._to_inventory_type(req.item)
            except ValueError:
                return False
            if inventory.count(req_item) < req.count:
                return False

        for out in recipe.outputs:
            try:
                self._to_inventory_type(out.item)
            except ValueError:
                return False
        return True
