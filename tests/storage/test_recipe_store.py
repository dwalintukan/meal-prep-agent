from models import Ingredient
from storage import IngredientStore, RecipeStore
from conftest import make_recipe


async def test_recipe_create_and_get(db):
    store = RecipeStore(db)
    recipe = make_recipe()
    await store.create(recipe)
    result = await store.get(1)
    assert result.name == "Pasta"
    assert len(result.ingredients) == 2
    assert result.ingredients[0].name == "Pasta"


async def test_recipe_get_all(db):
    store = RecipeStore(db)
    await store.create(make_recipe(1, "Pasta"))
    await store.create(make_recipe(2, "Salad"))
    results = await store.get_all()
    assert len(results) == 2
    names = {r.name for r in results}
    assert names == {"Pasta", "Salad"}


async def test_recipe_update(db):
    store = RecipeStore(db)
    await store.create(make_recipe())
    updated = make_recipe()
    updated.name = "Pasta Updated"
    updated.ingredients = [Ingredient(id=99, name="Spaghetti", unit="g", amount=300)]
    await store.update(updated)
    result = await store.get(1)
    assert result.name == "Pasta Updated"
    assert len(result.ingredients) == 1
    assert result.ingredients[0].name == "Spaghetti"


async def test_recipe_delete_cascades_ingredients(db):
    store = RecipeStore(db)
    ing_store = IngredientStore(db)
    await store.create(make_recipe())
    assert len(await ing_store.get_all()) == 2
    await store.delete(1)
    assert await store.get(1) is None
    assert len(await ing_store.get_all()) == 0


async def test_recipe_get_nonexistent_returns_none(db):
    assert await RecipeStore(db).get(999) is None


async def test_recipe_get_all_empty(db):
    assert await RecipeStore(db).get_all() == []


async def test_recipe_create_no_ingredients(db):
    recipe = make_recipe()
    recipe.ingredients = []
    await RecipeStore(db).create(recipe)
    result = await RecipeStore(db).get(1)
    assert result.ingredients == []


async def test_recipe_update_clears_ingredients(db):
    store = RecipeStore(db)
    await store.create(make_recipe())
    updated = make_recipe()
    updated.ingredients = []
    await store.update(updated)
    result = await store.get(1)
    assert result.ingredients == []


async def test_recipe_delete_nonexistent_no_error(db):
    await RecipeStore(db).delete(999)
