from datetime import datetime, date

from storage import (
    init_db,
    RecipeStore,
    IngredientStore,
    WeeklyPlanStore,
    ShoppingItemStore,
)
from models import Ingredient, Recipe, WeeklyPlan, ShoppingItem


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_recipe(id: int = 1, name: str = "Pasta") -> Recipe:
    return Recipe(
        id=id,
        name=name,
        instructions=["Boil water", "Cook pasta"],
        ingredients=[
            Ingredient(id=id * 10 + 1, name="Pasta", unit="g", amount=200),
            Ingredient(id=id * 10 + 2, name="Salt", unit="tsp", amount=1),
        ],
        servings=2,
        prep_minutes=5,
        cook_minutes=10,
        tags=["easy", "italian"],
        created_at=datetime(2026, 4, 20, 12, 0, 0),
    )


def make_plan(id: int = 1, recipe_ids: list[int] | None = None) -> WeeklyPlan:
    return WeeklyPlan(
        id=id,
        timestamp=date(2026, 4, 20),
        recipe_ids=recipe_ids if recipe_ids is not None else [1, 2, 3],
        created_at=datetime(2026, 4, 20, 12, 0, 0),
    )


def make_item(id: int = 1, weekly_plan_id: int = 1) -> ShoppingItem:
    return ShoppingItem(
        id=id,
        weekly_plan_id=weekly_plan_id,
        ingredient_name="Pasta",
        unit="g",
        amount=400,
    )


# ---------------------------------------------------------------------------
# RecipeStore
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# IngredientStore
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# WeeklyPlanStore
# ---------------------------------------------------------------------------


async def test_weekly_plan_create_and_get(db):
    store = WeeklyPlanStore(db)
    await store.create(make_plan())
    result = await store.get(1)
    assert result.recipe_ids == [1, 2, 3]
    assert result.timestamp == date(2026, 4, 20)


async def test_weekly_plan_get_all(db):
    store = WeeklyPlanStore(db)
    await store.create(make_plan(1))
    await store.create(make_plan(2))
    assert len(await store.get_all()) == 2


async def test_weekly_plan_update(db):
    store = WeeklyPlanStore(db)
    await store.create(make_plan())
    plan = await store.get(1)
    plan.recipe_ids = [4, 5, 6]
    await store.update(plan)
    result = await store.get(1)
    assert result.recipe_ids == [4, 5, 6]


async def test_weekly_plan_delete_cascades_shopping_items(db):
    plan_store = WeeklyPlanStore(db)
    item_store = ShoppingItemStore(db)
    await plan_store.create(make_plan())
    await item_store.create(make_item(weekly_plan_id=1))
    await plan_store.delete(1)
    assert await plan_store.get(1) is None
    assert await item_store.get_by_weekly_plan(1) == []


async def test_weekly_plan_get_nonexistent_returns_none(db):
    assert await WeeklyPlanStore(db).get(999) is None


async def test_weekly_plan_get_all_empty(db):
    assert await WeeklyPlanStore(db).get_all() == []


async def test_weekly_plan_create_empty_recipe_ids(db):
    plan = make_plan(recipe_ids=[])
    await WeeklyPlanStore(db).create(plan)
    result = await WeeklyPlanStore(db).get(1)
    assert result.recipe_ids == []


async def test_weekly_plan_delete_nonexistent_no_error(db):
    await WeeklyPlanStore(db).delete(999)


# ---------------------------------------------------------------------------
# ShoppingItemStore
# ---------------------------------------------------------------------------


async def test_shopping_item_create_and_get(db):
    await WeeklyPlanStore(db).create(make_plan())
    store = ShoppingItemStore(db)
    await store.create(make_item())
    result = await store.get(1)
    assert result.ingredient_name == "Pasta"
    assert result.amount == 400


async def test_shopping_item_get_all(db):
    await WeeklyPlanStore(db).create(make_plan(1))
    await WeeklyPlanStore(db).create(make_plan(2))
    store = ShoppingItemStore(db)
    await store.create(make_item(1, weekly_plan_id=1))
    await store.create(make_item(2, weekly_plan_id=2))
    assert len(await store.get_all()) == 2


async def test_shopping_item_get_by_weekly_plan(db):
    await WeeklyPlanStore(db).create(make_plan(1))
    await WeeklyPlanStore(db).create(make_plan(2))
    store = ShoppingItemStore(db)
    await store.create(make_item(1, weekly_plan_id=1))
    await store.create(make_item(2, weekly_plan_id=1))
    await store.create(make_item(3, weekly_plan_id=2))
    results = await store.get_by_weekly_plan(1)
    assert len(results) == 2
    assert all(r.weekly_plan_id == 1 for r in results)


async def test_shopping_item_update(db):
    await WeeklyPlanStore(db).create(make_plan())
    store = ShoppingItemStore(db)
    await store.create(make_item())
    updated = make_item()
    updated.amount = 999
    await store.update(1, updated)
    result = await store.get(1)
    assert result.amount == 999


async def test_shopping_item_delete(db):
    await WeeklyPlanStore(db).create(make_plan())
    store = ShoppingItemStore(db)
    await store.create(make_item())
    await store.delete(1)
    assert await store.get(1) is None


async def test_shopping_item_get_nonexistent_returns_none(db):
    assert await ShoppingItemStore(db).get(999) is None


async def test_shopping_item_get_all_empty(db):
    assert await ShoppingItemStore(db).get_all() == []


async def test_shopping_item_get_by_weekly_plan_no_items(db):
    await WeeklyPlanStore(db).create(make_plan())
    assert await ShoppingItemStore(db).get_by_weekly_plan(1) == []


async def test_shopping_item_get_by_weekly_plan_nonexistent_plan(db):
    assert await ShoppingItemStore(db).get_by_weekly_plan(999) == []


async def test_shopping_item_cascade_delete_via_plan(db):
    await WeeklyPlanStore(db).create(make_plan())
    store = ShoppingItemStore(db)
    await store.create(make_item())
    await WeeklyPlanStore(db).delete(1)
    assert await store.get_by_weekly_plan(1) == []


async def test_shopping_item_delete_nonexistent_no_error(db):
    await ShoppingItemStore(db).delete(999)
