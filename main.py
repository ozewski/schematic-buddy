from pprint import pprint
import sys
import time


from litemapy import Schematic

from schem.item import Item, Stack, Tag
from schem.analyzer import SchematicAnalyzer
from schem.recipe import Recipe, RecipeMethod
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

#for item, recipes in app.config.all_recipes.items():
#    print(item.pretty_name)
#    for recipe in recipes:
#        print(recipe)
#    print()

# Next steps:
# - create RecipeCollection (set-like type?)
# - operations:
#    - by_method(method: str) -> RecipeCollection
# - keep record of recipes per method in __init__()?
