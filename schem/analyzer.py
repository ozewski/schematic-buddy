from litemapy import Schematic

from .item import Item


class SchematicAnalyzer:
    schematic: Schematic
    materials: dict[Item, int]

    def __init__(self, schematic: Schematic):
        self._schematic = schematic
        self._calculate_material_counts()

    def _calculate_material_counts(self):
        self._materials = {}
        for region in self.schematic.regions.values():
            for x, y, z in region.allblockpos():
                block = region.getblock(x, y, z)
                if block.blockid != "minecraft:air":
                    item = Item.from_identifier(block.blockid)
                    c = self._materials.get(item, 0)
                    self._materials[item] = c + 1

    @classmethod
    def load(cls):
        ...

    @property
    def schematic(self):
        return self._schematic

    @property
    def materials(self):
        return self._materials

