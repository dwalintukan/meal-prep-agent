from typing import Annotated
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.types import Command

from agent import MealPlanWorkflow, ParseRecipeWorkflow


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
        ).run()
        return result

    @tool
    async def get_meal_plan() -> str:
        pass

    @tool
    async def parse_recipe(
        url: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> str:
        """Parse and preview a recipe from a URL. The user will confirm before it's saved."""
        reply, recipe = await ParseRecipeWorkflow(
            args["model_agent"], url, args["prompt_store"]
        ).run()
        content = "\n\n".join(reply) if isinstance(reply, list) else str(reply)

        return Command(
            update={"pending_recipe": recipe},
            messages=[ToolMessage(content=content, tool_call_id=tool_call_id)],
        )
