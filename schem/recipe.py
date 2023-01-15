from collections import defaultdict
from typing import List, Optional, Union

from .item import Item, Stack


class Recipe:
    """Defines a recipe that uses ingredients and creates a result through a specific method.

    - Recipe(result, ingredients, method)"""

    method: str  # RecipeMethod.SMELTING, etc., or None
    ingredients: List[Stack]  # ingredients must be stacks of items
    result: Stack  # result must be a specific item

    def __init__(self, result: Stack, ingredients: List[Stack], method: str):
        if method not in RecipeMethod.ALL:
            raise ValueError("Unrecognized item recipe type (see RecipeMethod.ALL)")
        self.method = method
        self.ingredients = ingredients
        self.result = result

    def __repr__(self):
        return f"<Recipe method={self.method} ingredients={self.ingredients} result={self.result}>"


class RecipeMethod:
    CRAFTING_SHAPED = "minecraft:crafting_shaped"
    CRAFTING_SHAPELESS = "minecraft:crafting_shapeless"
    BLASTING = "minecraft:blasting"
    CAMPFIRE_COOKING = "minecraft:campfire_cooking"
    SMELTING = "minecraft:smelting"
    SMITHING = "minecraft:smithing"
    SMOKING = "minecraft:smoking"
    STONECUTTING = "minecraft:stonecutting"
    ALL = {CRAFTING_SHAPED, CRAFTING_SHAPELESS, BLASTING, CAMPFIRE_COOKING, SMELTING, SMOKING, STONECUTTING}
    ALL_MULTI_INGREDIENT = {CRAFTING_SHAPED, CRAFTING_SHAPELESS}
    ALL_SINGLE_INGREDIENT = ALL - ALL_MULTI_INGREDIENT


class RecipeCollection:
    """Set-like type that allows for storage of recipes for one particular Item, with various query methods."""
    recipes: set[Recipe]

    def __init__(self):
        self.recipes = set()

    def add(self, recipe: Recipe) -> None:
        self.recipes.add(recipe)

    def remove(self, recipe: Recipe) -> None:
        self.recipes.remove(recipe)

    def __iter__(self):
        return iter(self.recipes)

    def __repr__(self):
        return repr(self.recipes)


class RecipeConfiguration:
    """Represents the choices a user makes for which recipe to use for which item."""
    choices: dict[Item, Recipe]  # items without recipes should receive "None" value

    def __init__(self, recipes: Optional[List[Recipe]] = None):
        ...

    @classmethod
    def from_file(cls, path: str) -> "RecipeConfiguration":
        ...  # open and validate path
        c = RecipeConfiguration()
        ...  # add items to configuration
        return c


class RecipeTree:
    target: Stack
    base: Stack
    hierarchy: List[Stack]

    def __init__(self, target: Stack):
        self.target = self.base = target

    def expand(self, config: RecipeConfiguration):
        """Expands the recipe tree by checking the current base and seeing if it should be processed."""
