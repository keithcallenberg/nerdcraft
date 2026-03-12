"""Crafting recipe engine backed by config/recipes.json."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

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
    station: Optional[str]
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
                station=raw_recipe.get("station"),
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

    def _to_inventory_type(self, item_name: str) -> InventoryType:
        upper = item_name.upper()
        if upper in BlockType.__members__:
            return BlockType[upper]
        if upper in ItemType.__members__:
            return ItemType[upper]
        raise ValueError(f"Unknown recipe item type: {item_name}")

    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        """Get a recipe by ID."""
        return self._recipes.get(recipe_id)

    def all_recipes(self) -> list[Recipe]:
        """Return all known recipes in load order."""
        return list(self._recipes.values())

    def available_recipes(self, inventory: Inventory) -> list[Recipe]:
        """Return recipes that can currently be crafted from inventory."""
        return [
            recipe
            for recipe in self._recipes.values()
            if self._can_craft(inventory, recipe)
        ]

    def craft(self, inventory: Inventory, recipe_id: str) -> bool:
        """Craft a recipe by ID, mutating inventory. Returns True on success."""
        recipe = self._recipes.get(recipe_id)
        if recipe is None:
            return False

        if not self._can_craft(inventory, recipe):
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

    def _can_craft(self, inventory: Inventory, recipe: Recipe) -> bool:
        # Station requirements are currently represented as owning the station item.
        if recipe.station is not None:
            try:
                station_item = self._to_inventory_type(recipe.station)
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
