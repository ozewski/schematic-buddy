from typing import Optional, Generator

from litemapy import Schematic

from .item import Item, ItemStack
from .recipe import RecipeConfiguration, RecipeCollection


class ExpansionException(Exception):
    """An exception occured during the expansion of a RecipeNode."""


class RecipeNode:
    item: Item  # target item
    count: int
    parent: Optional["RecipeNode"] = None  # top level node will have no parent
    children: list["RecipeNode"]
    final: bool

    def __init__(self, item: ItemStack):
        self.item = item.component
        self.count = item.count
        self.children = []
        self.final = False

    def expand(self, config: RecipeConfiguration):
        """Expands the recipe tree by checking the current base and seeing if it should be processed."""
        if not config.is_set(self.item):
            raise ExpansionException(f"Preferred recipe for {self.item} is not configured")
        recipe = config.get_recipe(self.item)
        if recipe:
            print(self.item.name)
            print(recipe)
            print()
        else:
            self.final = True

    def __repr__(self) -> str:
        return f"<Node item={self.item} (count={self.count}) children={len(self.children)}>"


class RequirementAnalyzer:
    """A type simplifying the deduction of recipe ingredients based on user choices."""
    schematic: Schematic
    config: RecipeConfiguration
    recipes: dict[Item, RecipeCollection]
    materials: dict[Item, int]
    trees: list[RecipeNode]
    outstanding_nodes: list[RecipeNode]

    def __init__(self, schematic: Schematic, config: RecipeConfiguration, recipes: dict[Item, RecipeCollection]):
        self.schematic = schematic
        self.config = config
        self.recipes = recipes
        self.trees = []
        self.outstanding_nodes = []
        self._calculate_material_counts()

        for item, recipes in self.recipes.items():
            if len(recipes) == 1:
                (r), = recipes  # used to get sole member because recipes is unordered and has no indexes
                if not r.complex:
                    self.config.choose(item, r)

    def outstanding_requirements(self) -> Generator[Item, None, None]:
        """Returns all items that have not been assigned a recipe within the recipe configuration."""
        for node in self.outstanding_nodes:
            if not self.config.is_set(node.item):
                yield node.item

    def calculate_single_level(self):
        """Calculates all children of non-finalized nodes."""
        for node in self.outstanding_nodes:
            node.expand(self.config)

        self._calculate_outstanding_nodes()

    def _calculate_outstanding_nodes(self):
        new_nodes = []
        for node in self.outstanding_nodes:
            if not node.final:
                if node.children:
                    for child in node.children:
                        yield child
                        new_nodes.append(child)  # if children have been generated, they replace their parent
                else:
                    new_nodes.append(node)  # otherwise, the parent remains

        self.outstanding_nodes = new_nodes

    def _calculate_material_counts(self):
        materials = {}
        for region in self.schematic.regions.values():
            for x, y, z in region.allblockpos():
                block = region.getblock(x, y, z)
                if block.blockid != "minecraft:air":
                    item = Item.from_identifier(block.blockid)
                    c = materials.get(item, 0)
                    materials[item] = c + 1

        for item, count in materials.items():
            self.trees.append(RecipeNode(ItemStack(item, count)))

        self.materials = materials
        self.outstanding_nodes = self.trees.copy()
