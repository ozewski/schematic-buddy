from collections import defaultdict
# import itertools
import json
from pprint import pprint
from time import time
from typing import Optional, Iterator, Union
import zipfile

from litemapy import Schematic

from schem.analyzer import RequirementAnalyzer
from schem.item import ComplexRecipeComponent, InterchangeableItem, InterchangeableItemStack, Item, ItemStack, \
    RecipeComponent, Tag, TagStack
from schem.recipe import Recipe, RecipeCollection, RecipeConfiguration, RecipeMethod


class AppConfiguration:
    jar_path: Optional[str]
    all_recipes: dict[Item, RecipeCollection]

    def __init__(self):
        self.jar_path = None
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
        item = recipe.result.component
        if item not in self.all_recipes:
            self.all_recipes[item] = RecipeCollection()
        self.all_recipes[item].add(recipe)


class App:
    config: AppConfiguration
    active_schematic: Optional[RequirementAnalyzer]

    def __init__(self):
        self.config = AppConfiguration()
        ...

    def analyze(self, schematic: Schematic, config: RecipeConfiguration):
        """Opens the analysis screen for a schematic within the app."""
        self.active_schematic = RequirementAnalyzer(schematic, config, self.config.all_recipes)
        print(f"> SCHEMATIC LOADED: ({schematic.name})")
        if self.active_schematic.outstanding_nodes:
            print("> This schematic has some items with multiple recipes. Enter your selections below.\n\n-----")
            while True:
                reqs = list(self.active_schematic.outstanding_requirements())
                for item in reqs:  # iterate through every item without a recipe
                    choice = self.prompt_item_choice(item)
                    if choice:
                        if choice.complex:  # item needs its complex ingredients picked as well
                            ingredient_choices = self.prompt_complex_ingredients_choice(choice)
                            choice.ingredients = [  # convert original complex ingredients into ItemStacks
                                ItemStack(ingredient_choices[stack.component], stack.count)
                                if stack.component in ingredient_choices else stack
                                for stack in choice.ingredients
                            ]
                        print("\n-----")
                    config.choose(item, choice)
                self.active_schematic.calculate_single_level()
                break

    def prompt_item_choice(self, item: Item) -> Optional[Recipe]:
        """Prompts a user's choice for an item recipe based on all available recipes. The resulting Recipe returned
        by this method may still be complex and can be further reduced with prompt_complex_ingredients_choice()."""
        recipes = self.config.all_recipes.get(item, None)
        if not recipes:
            return None

        print(f"\nSELECT RECIPE: {item.name}")
        recipes = list(recipes)
        for i, recipe in enumerate(recipes, start=1):
            print(f"  {i}. {recipe.ingredients_shorthand()} - "
                  f"{recipe.method.short_name.lower()} recipe, makes {recipe.result.count}")

        print()
        choice = self.validated_choice_input(len(recipes))
        return recipes[choice - 1]

    def prompt_complex_ingredients_choice(self, recipe: Recipe) -> dict[RecipeComponent, Item]:
        choices = {}
        if not recipe.complex:
            return choices
        print("\n> Make selections for this recipe's ingredients:")
        for ingredient in recipe.ingredients:
            if ingredient.component.complex:
                # ingredient is a Tag or InterchangeableItem
                print(f"\n- {ingredient.count}x of:")
                if type(ingredient) is TagStack:
                    opts = ingredient.component.flatten()
                else:
                    opts = ingredient.component.members
                print(" or\n".join(f"  {i}. {x.name}" for i, x in enumerate(opts, start=1)) + "\n")
                choice = self.validated_choice_input(len(opts))
                choices[ingredient.component] = opts[choice - 1]

        return choices

    def validated_choice_input(self, maximum: int) -> int:
        while True:
            choice = input("Choose >> ")
            try:  # todo: more comprehensive input validation with user error messages
                choice = int(choice)
                assert choice <= maximum
                break
            except (ValueError, AssertionError):
                continue
        return choice

    def load_all_data(self):
        """Loads all item, recipe, and tag data required to perform recipe calculations."""
        if not self.config.jar_path:
            raise ValueError("No jar path set; use App.config.set_jar_path(...)")
        self.load_items()
        self.load_tags()
        self.load_recipe_methods()
        self.load_recipes()

    def load_items(self):
        zf = zipfile.Path(self.config.jar_path, "assets/minecraft/lang/en_us.json")
        data = json.loads(zf.read_text(encoding="utf-8"))
        for entry in data.items():
            name, pretty_name = entry
            name = name.split(".")
            if name[0] in ("block", "item") and name[1] == "minecraft" and len(name) == 3:
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
            if RecipeMethod.exists(data["type"]):
                if type(x := data["result"]) is str:
                    result = Item.from_identifier(x)
                    count = data.get("count", 1)
                else:
                    result = Item.from_identifier(x["item"])
                    count = x.get("count", 1)

                result = ItemStack(result, count)  # defines: recipe result (as ItemStack)
                method = RecipeMethod.from_identifier(data["type"])  # defines: recipe method

                if "ingredient" in data:  # non-crafting recipe; single ingredient slot
                    i = data["ingredient"]
                    if type(i) == list:  # multiple item options
                        ingredient = InterchangeableItemStack(
                            InterchangeableItem(list(map(lambda n: Item.from_identifier(n["item"]), i)))
                        )
                    elif "tag" in i:  # single tag
                        ingredient = TagStack(Tag.from_identifier(i["tag"]))
                    else:  # single item
                        ingredient = ItemStack(Item.from_identifier(i["item"]))

                    self.config.register_recipe(Recipe(result, [ingredient], method))

                elif method.identifier == "minecraft:crafting_shapeless":  # shapeless crafting recipe
                    r = data["ingredients"]
                    (k, v), = r[0].items()
                    if k == "tag":  # ingredient is a singular tag ingredient
                        self.config.register_recipe(Recipe(result, [TagStack(Tag.from_identifier(v))], method))
                    else:  # ingredient is list of components
                        r = [  # prepare objects
                            Item.from_identifier(j["item"])
                            if type(j) is dict else InterchangeableItem([Item.from_identifier(x["item"]) for x in j])
                            for j in r
                        ]
                        stacks = defaultdict(int)
                        for component in r:  # count number of each component
                            stacks[component] += 1

                        self.config.register_recipe(
                            Recipe(result, [
                                ItemStack(k, v) if type(k) is Item else InterchangeableItemStack(k, v)
                                for k, v in stacks.items()
                            ], method)
                        )

                else:  # shaped crafting recipe
                    pattern = "".join(data["pattern"])  # convert pattern list to string for str.count use
                    i = data["key"]
                    i_objects = []
                    for k, v in i.items():  # iterate over each pattern association
                        c = pattern.count(k)
                        if "tag" in v:  # a tag
                            i_objects.append(TagStack(Tag.from_identifier(v["tag"]), c))
                        elif type(v) is list:  # list of options; convert to InterchangeableItem
                            i_objects.append(
                                InterchangeableItemStack(
                                    InterchangeableItem([Item.from_identifier(x["item"]) for x in v]), c))
                        else:  # a specific item
                            i_objects.append(ItemStack(Item.from_identifier(v["item"]), c))

                    self.config.register_recipe(Recipe(result, i_objects, method))
                    # for recipe in itertools.product(*i_objects):  # iterate through recipes, count their ingredients
                    #     self.config.register_recipe(Recipe(result, list(recipe), method))

    def load_recipe_methods(self):
        RecipeMethod.register("minecraft:crafting_shaped", "Crafting (shaped)", "Crafting")
        RecipeMethod.register("minecraft:crafting_shapeless", "Crafting (shapeless)", "Crafting")
        RecipeMethod.register("minecraft:blasting", "Blasting")
        RecipeMethod.register("minecraft:campfire_cooking", "Campfire Cooking", "Campfire")
        RecipeMethod.register("minecraft:smelting", "Smelting")
        # RecipeMethod.register("minecraft:smithing", "Smithing")
        RecipeMethod.register("minecraft:smoking", "Smoking")
        RecipeMethod.register("minecraft:stonecutting", "Stonecutting")