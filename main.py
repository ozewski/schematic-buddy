from pprint import pprint
import sys
import time


from litemapy import Schematic

from schem.item import Item, Stack, Tag
from schem.analyzer import RequirementAnalyzer
from schem.recipe import Recipe, RecipeMethod, RecipeConfiguration
from app import App, AppConfiguration

"""
schem = Schematic.load("deer_statue.litematic")
s = SchematicAnalyzer(schem)
print(s.materials)
print(s.schematic)
"""

app = App()
app.config.set_jar_path(sys.argv[1])
app.load_all_data()
print()
app.analyze(Schematic.load("1.18 Base.litematic"), RecipeConfiguration())
