from storage.recipe_store import RecipeStore


def meal_plan_workflow() -> str:
    # Fetch all recipes
    recipes = RecipeStore()
    recipes.get_all()

    # Fetch previous weekly_plan

    # Call LLM to get new plan with minimal overlap

    # Validate recipe_ids

    # Aggregate ingredients

    # Create shopping_items

    # Create weekly_plan
