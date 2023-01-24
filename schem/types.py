from typing import Any, Hashable, TypeVar

S = TypeVar("S", bound="_Identified")
T = TypeVar("T", bound=Hashable)


class Identified:
    all: dict[Any, S]
    identifier: T

    @classmethod
    def from_identifier(cls, identifier: T) -> S:
        items = cls.all
        if not items:
            raise ValueError("No entries registered")
        if identifier not in items:
            raise ValueError("Unknown identifier: " + identifier)
        return items[identifier]

    @classmethod
    def exists(cls, identifier: T) -> bool:
        """Returns True if the entry has been registered."""
        return identifier in cls.all

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.identifier}>"

    def __hash__(self):
        return hash((self.__class__.__name__, self.identifier))

    def __eq__(self, other):
        return type(other) is self.__class__ and self.identifier == other.identifier
