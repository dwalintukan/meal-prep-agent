from storage import IngredientStore, RecipeStore
from conftest import make_recipe


async def test_ingredient_create_and_get(db):
    await RecipeStore(db).create(make_recipe())
    store = IngredientStore(db)
    result = await store.get(11)
    assert result.name == "Pasta"
    assert result.amount == 200


async def test_ingredient_get_all(db):
    await RecipeStore(db).create(make_recipe(1))
    await RecipeStore(db).create(make_recipe(2))
    all_ings = await IngredientStore(db).get_all()
    assert len(all_ings) == 4


async def test_ingredient_update(db):
    await RecipeStore(db).create(make_recipe())
    store = IngredientStore(db)
    ing = await store.get(11)
    ing.amount = 500
    await store.update(ing)
    result = await store.get(11)
    assert result.amount == 500


async def test_ingredient_delete(db):
    await RecipeStore(db).create(make_recipe())
    store = IngredientStore(db)
    await store.delete(11)
    assert await store.get(11) is None


async def test_ingredient_get_nonexistent_returns_none(db):
    assert await IngredientStore(db).get(999) is None


async def test_ingredient_get_all_empty(db):
    assert await IngredientStore(db).get_all() == []


async def test_ingredient_cascade_delete_via_recipe(db):
    await RecipeStore(db).create(make_recipe())
    await RecipeStore(db).delete(1)
    assert await IngredientStore(db).get_all() == []
