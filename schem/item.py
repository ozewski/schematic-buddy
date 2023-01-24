from abc import ABC
from typing import Any, List, Optional, TypeVar, Union

from numpy import ndarray

from .types import Identified


class RecipeComponent(ABC):
    """Represents an object which can be a member of a recipe."""
    complex: bool = False


class ComplexRecipeComponent(RecipeComponent):
    """Represents a RecipeComponent which is complex; meaning it has a sublist of members which can represent its
    place within a recipe."""
    complex = True
    members: list


class Item(RecipeComponent, Identified):
    """Represents a Minecraft item."""
    identifier: str  # minecraft:white_stained_glass
    name: str  # White Stained Glass
    icon: Optional[ndarray]  # cv2.imread

    all: dict[str, "Item"] = {}

    @staticmethod
    def register(identifier: str, name: str, icon: Optional[ndarray] = None) -> "Item":
        i = Item()
        i.identifier = identifier
        i.name = name
        i.icon = icon
        Item.all.update({identifier: i})
        return i


class InterchangeableItem(ComplexRecipeComponent):
    """Used to represent a recipe component that can be interchanged between multiple items.

    An InterchangeableItem behaves differently from a Tag in the following way:

    - Tags have a unique Minecraft identifier (eg. minecraft:logs_that_burn).
    - Tags are global, meaning their choices will remain the same for all recipes.
    - When simplified, a TagStack will only represent one type of item in a recipe regardless of its quantity. An
      InterchangeableItemStack of quantity > 1 may consist of any combination of all members of the
      InterchangeableItem, meaning a mix of items is valid in the recipe."""

    members: list[Item]

    def __init__(self, members: list[Item]):
        self.members = members

    def __repr__(self):
        return f"<InterchangeableItem members={self.members}>"


class Tag(ComplexRecipeComponent, Identified):
    """Represents a tag; a collection of items or other tags."""
    identifier: str  # minecraft:enderman_holdable
    members: List[Union[Item, "Tag"]]

    all: dict[str, "Tag"] = {}

    @staticmethod
    def register(identifier: str, members: List[Union[Item, "Tag"]]) -> "Tag":
        t = Tag()
        t.identifier = identifier
        t.members = members
        Tag.all.update({identifier: t})
        return t  # courtesy

    def _flatten_tags(self, tag: "Tag"):
        for x in tag.members:
            if type(x) is Item:
                yield x
            else:
                yield from self._flatten_tags(x)

    def flatten(self) -> List[Item]:
        """Returns all items that fall within a tag."""
        return list(self._flatten_tags(self))

    def __repr__(self):
        return f"<Tag {self.identifier} members=[{'...' if self.members else ''}]>"


class Stack:
    """Represents a generic stack of a RecipeComponent (Item, Tag, or InterchangeableItem)."""
    component: RecipeComponent
    count: int

    def __init__(self, component: RecipeComponent, count: Optional[int] = 1):
        self.component = component
        self.count = count

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} component={self.component} count={self.count}>"


class ItemStack(Stack):
    """A stack specifically representing an Item."""
    component: Item


class TagStack(Stack):
    """A stack specifically representing a Tag."""
    component: Tag


class InterchangeableItemStack(Stack):
    """A stack specifically representing an InterchangeableItem."""
    component: InterchangeableItem
