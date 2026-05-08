from anthropic import AsyncAnthropic
from agent.classifier import Intent, classify
from agent.workflows.chat import ChatWorkflow
from agent.workflows.meal_plan import MealPlanWorkflow
from storage import RecipeStore, WeeklyPlanStore, ShoppingItemStore


async def route(
    message: str,
    client: AsyncAnthropic,
    recipe_store: RecipeStore,
    weekly_plan_store: WeeklyPlanStore,
    shopping_item_store: ShoppingItemStore,
) -> str:
    intent = await classify(message, client)
    match intent:
        case Intent.PLAN:
            return await MealPlanWorkflow(
                client, recipe_store, weekly_plan_store, shopping_item_store
            ).run()

        case Intent.CHAT:
            return ChatWorkflow().run()
