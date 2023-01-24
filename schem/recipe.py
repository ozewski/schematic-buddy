from typing import List, Optional, TypeVar

from .item import Item, InterchangeableItemStack, ItemStack, RecipeComponent, Stack, TagStack
from .types import Identified


def _item_multi_select(opts: list[Item], limit: int = 2) -> str:
    result = " or ".join(map(lambda x: x.name, opts[:limit]))
    return (result + " or (...)") if len(opts) > limit else result


class RecipeMethod(Identified):
    identifier: str
    name: str
    short_name: str

    all: dict[str, "RecipeMethod"] = {}

    @staticmethod
    def register(identifier: str, name: str, short_name: Optional[str] = None) -> "RecipeMethod":
        i = RecipeMethod()
        i.identifier = identifier
        i.name = name
        i.short_name = short_name or name
        RecipeMethod.all.update({identifier: i})
        return i


class Recipe:
    """Defines a recipe that uses ingredients and creates a result through a specific method.

    A "complex" recipe is one that includes at least one non-item ingredient (a Tag or InterchangeableItem). Simple
    recipes consist solely of Items."""
    method: RecipeMethod  # RecipeMethod.from_identifier("minecraft:smelting")
    ingredients: List[Stack]  # ingredients must be stacks of items, tags, or interchangable items
    result: ItemStack  # result must be a specific item

    def __init__(self, result: ItemStack, ingredients: List[Stack], method: RecipeMethod):
        self.method = method
        self.ingredients = ingredients
        self.result = result

    # noinspection PyUnresolvedReferences
    def ingredients_shorthand(self) -> str:
        result = []
        for stack in self.ingredients:
            if type(stack) is TagStack:
                result.append(f"{stack.count}x ({_item_multi_select(stack.component.flatten())})")
            elif type(stack) is InterchangeableItemStack:
                result.append(f"{stack.count}x ({_item_multi_select(stack.component.members)})")
            else:
                result.append(f"{stack.count}x {stack.component.name}")
        return ", ".join(result)

    @property
    def complex(self):
        """Returns whether or not the recipe is complex; meaning it consists of at least one complex ingredient."""
        return any(ingredient.component.complex for ingredient in self.ingredients)

    def __repr__(self):
        return f"<Recipe method={self.method} ingredients={self.ingredients} result={self.result}>"


class RecipeCollection:
    """Set-like type that allows for storage of recipes for one particular Item, with various query methods."""
    recipes: set[Recipe]
    sort_order: list[RecipeMethod] = None

    def __init__(self):
        self.recipes = set()

    @staticmethod
    def set_sort_order(order: list[RecipeMethod]):
        """Sets the order that recipes will be yielded during iteration."""
        RecipeCollection.sort_order = order

    def add(self, recipe: Recipe) -> None:
        self.recipes.add(recipe)

    def remove(self, recipe: Recipe) -> None:
        self.recipes.remove(recipe)

    def _iterate_sorted(self):
        for method in self.sort_order:  # iterates in list order
            for recipe in self.recipes:
                if recipe.method == method:
                    yield recipe

    def __iter__(self):
        if self.sort_order:
            return self._iterate_sorted()
        return iter(self.recipes)

    def __len__(self):
        return len(self.recipes)

    def __repr__(self):
        return repr(self.recipes)


class RecipeConfiguration:
    """Represents the choices a user makes for which recipe to use for each recipe component."""
    choices: dict[RecipeComponent, Optional[Recipe]]  # items without recipes should receive "None" value

    def __init__(self):
        self.choices = {}

    def is_set(self, component: RecipeComponent):
        """Returns whether or not a component has been assigned a recipe."""
        return component in self.choices

    def get_recipe(self, component: RecipeComponent) -> Optional[Recipe]:
        if not self.is_set(component):
            raise ValueError("Component choice is unset")
        return self.choices.get(component)

    def choose(self, component: RecipeComponent, recipe: Optional[Recipe]):
        if recipe and recipe.complex:
            for ingredient in recipe.ingredients:
                if ingredient.component not in self.choices:
                    raise ValueError(f"Recipe for ingredient {ingredient.component} is unset")

        self.choices[component] = recipe

    def choose_all(self, recipes: dict[RecipeComponent, Optional[Recipe]]):
        for component, recipe in recipes:
            self.choose(component, recipe)

    @classmethod
    def from_file(cls, path: str) -> "RecipeConfiguration":
        ...  # open and validate path
        c = RecipeConfiguration()
        ...  # add items to configuration
        return c
