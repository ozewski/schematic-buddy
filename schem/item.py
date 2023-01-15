from typing import Any, List, Optional, TypeVar, Union

from numpy import ndarray

S = TypeVar("S", bound="_Identified")


class _Identified:
    all: dict[str, S]
    identifier: Any

    @classmethod
    def from_identifier(cls, identifier: str) -> S:
        items = cls.all
        if not items:
            raise ValueError("No entries registered")
        if identifier not in items:
            raise ValueError("Unknown identifier: " + identifier)
        return items[identifier]

    @classmethod
    def exists(cls, identifier: str) -> bool:
        """Returns True if the entry has been registered."""
        if _Identified not in cls.__bases__:
            raise NotImplemented("Must be called on the subclass")
        return identifier in cls.all

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.identifier}>"

    def __hash__(self):
        return hash((self.__class__.__name__, self.identifier))

    def __eq__(self, other):
        return type(other) is self.__class__ and self.identifier == other.identifier


class Item(_Identified):
    """Represents a Minecraft item."""
    identifier: str  # minecraft:white_stained_glass
    pretty_name: str  # White Stained Glass
    icon: Optional[ndarray]  # cv2.imread

    all: dict[str, "Item"] = {}

    @staticmethod
    def register(identifier: str, pretty_name: str, icon: Optional[ndarray] = None) -> "Item":
        i = Item()
        i.identifier = identifier
        i.pretty_name = pretty_name
        i.icon = icon
        Item.all.update({identifier: i})
        return i


class Tag(_Identified):
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
        return f"<Tag {self.identifier} members={self.members}>"


class Stack:
    """Represents a stack of a specific item (quantified)."""
    item: Item
    count: int

    def __init__(self, item: Item, count: Optional[int] = 1):
        self.item = item
        self.count = count

    def __repr__(self) -> str:
        return f"<Stack item={self.item} count={self.count}>"
