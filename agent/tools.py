from langchain_core.messages import tool
from agent import MealPlanWorkflow


def make_tools(args):
    @tool
    async def create_meal_plan() -> str:
        """Generate and persist a weekly meal plan from saved recipes."""
        result = await MealPlanWorkflow(
            args["model_agent"],
            args["recipe_store"],
            args["weekly_plan_store"],
            args["shopping_item_store"],
            args["prompt_store"],
            args["vector_store"],
        )
        return result

    @tool
    async def get_meal_plan() -> str:
        pass
