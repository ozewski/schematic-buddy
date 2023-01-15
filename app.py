from collections import defaultdict
import itertools
import json
from time import time
from typing import Optional, Iterator, Union
import zipfile

from schem.recipe import Recipe, RecipeCollection, RecipeConfiguration, RecipeMethod
from schem.item import Item, Tag, Stack


class AppConfiguration:
    jar_path: Optional[str]
    recipe_config: Optional[RecipeConfiguration]
    all_recipes: dict[Item, RecipeCollection]

    def __init__(self):
        self.jar_path = None
        self.recipe_config = None
        self.all_recipes = {}

    def set_jar_path(self, path: str, validate: bool = True) -> None:
        if validate:
            try:
                zf = zipfile.Path(path)
            except FileNotFoundError:
                raise ValueError("Path does not exist")
            for p in ("assets", "data"):
                sub_path = zf / p
                if not (sub_path.exists() and sub_path.is_dir()):
                    raise ValueError(f"Jar file is invalid ('/{p}' folder missing)")

        self.jar_path = path

    def register_recipe(self, recipe: Optional[Recipe]) -> None:
        """Adds a recipe to the master list of recipes, associating it with its resulting item."""
        item = recipe.result.item
        if item not in self.all_recipes:
            self.all_recipes[item] = RecipeCollection()
        self.all_recipes[item].add(recipe)


class App:
    config: AppConfiguration

    def __init__(self):
        self.config = AppConfiguration()
        self.config.recipe_config = RecipeConfiguration()
        ...

    def load_all_data(self):
        """Loads all item, recipe, and tag data required to perform recipe calculations."""
        if not self.config.jar_path:
            raise ValueError("No jar path set; use App.config.set_jar_path(...)")
        start = time()
        self.load_items()
        print(time() - start)
        self.load_tags()
        print(time() - start)
        self.load_recipes()
        print(time() - start)

    def load_items(self):
        zf = zipfile.Path(self.config.jar_path, "assets/minecraft/lang/en_us.json")
        data = json.loads(zf.read_text(encoding="utf-8"))
        for entry in data.items():
            name, pretty_name = entry
            name = name.split(".")
            if name[0] in ("block", "item") and len(name) == 3:
                Item.register(f"minecraft:{name[2]}", pretty_name)

    def load_tags(self):
        zf = zipfile.Path(self.config.jar_path, "data/minecraft/tags/items/")
        data = {
            f"minecraft:{fp.name.split('.')[0]}": json.loads(fp.read_text(encoding="utf-8"))["values"]
            for fp in zf.iterdir()
        }

        def process(entry: dict) -> Iterator[Union[Tag, Item]]:
            for t in entry:
                if t.startswith("#"):
                    name = t[1:]
                    new_tag = Tag.register(name, list(process(data[name])))
                    yield new_tag
                else:
                    yield Item.from_identifier(t)

        for tag, entry in data.items():
            if not Tag.exists(tag):
                Tag.register(tag, list(process(entry)))

    def load_recipes(self):
        zf = zipfile.Path(self.config.jar_path, "data/minecraft/recipes/")
        for f in zf.iterdir():
            data = json.loads(f.read_text(encoding="utf-8"))
            method = data["type"]  # defines: recipe method
            if method in RecipeMethod.ALL:
                if type(x := data["result"]) is str:
                    result = Item.from_identifier(x)
                    count = data.get("count", 1)
                else:
                    result = Item.from_identifier(x["item"])
                    count = x.get("count", 1)

                result = Stack(result, count)  # defines: recipe result (as ItemStack)

                if "ingredient" in data:  # non-crafting recipe; single ingredient slot
                    i = data["ingredient"]
                    i = i if type(i) is list else [i]
                    for item in i:
                        (k, v), = item.items()  # fetch data from the only key
                        if k == "tag":  # ingredient is a tag that needs to be processed into multiple recipes
                            tag = Tag.from_identifier(v)
                            for entry in tag.flatten():
                                self.config.register_recipe(Recipe(result, [Stack(entry)], method))
                        else:  # ingredient is an item
                            self.config.register_recipe(Recipe(result, [Stack(Item.from_identifier(v))], method))

                elif method == RecipeMethod.CRAFTING_SHAPELESS:  # shapeless crafting recipe
                    i = data["ingredients"]
                    (k, v), = i[0].items()

                    if k == "tag":  # ingredient is a singular tag ingredient
                        tag = Tag.from_identifier(v)
                        for entry in tag.flatten():
                            self.config.register_recipe(Recipe(result, [Stack(entry)], method))
                    else:  # ingredient is list of items
                        i = [  # prepares list for cartesian product
                            [Item.from_identifier(j["item"])]
                            if type(j) is dict else [Item.from_identifier(x["item"]) for x in j]
                            for j in i
                        ]
                        for recipe in itertools.product(*i):  # iterate through recipes, count their ingredients
                            stacks = defaultdict(int)
                            for item in recipe:
                                stacks[item] += 1
                            self.config.register_recipe(
                                Recipe(result, [Stack(k, v) for k, v in stacks.items()], method))

                else:  # shaped crafting recipe
                    pattern = "".join(data["pattern"])  # convert pattern list to string for str.count use
                    i = data["key"]
                    i_objects = []
                    for k, v in i.items():  # iterate over each pattern association
                        c = pattern.count(k)
                        if "tag" in v:  # flatten tag to Items
                            i_objects.append([Stack(x, c) for x in Tag.from_identifier(v["tag"]).flatten()])
                        elif type(v) is list:  # convert all members to Items
                            i_objects.append([Stack(Item.from_identifier(x["item"]), c) for x in v])
                        else:  # a specific item
                            i_objects.append([Stack(Item.from_identifier(v["item"]), c)])

                    for recipe in itertools.product(*i_objects):  # iterate through recipes, count their ingredients
                        self.config.register_recipe(Recipe(result, list(recipe), method))
