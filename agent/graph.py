from langchain_core.language_models import BaseChatModel
from langchain_core.vectorstores import VectorStore
from agent.classifier import classify
from agent.state import BotState
from storage import RecipeStore, WeeklyPlanStore, ShoppingItemStore


def create_graph(
    model_classifier: BaseChatModel,
    model_agent: BaseChatModel,
    recipe_store: RecipeStore,
    weekly_plan_store: WeeklyPlanStore,
    shopping_item_store: ShoppingItemStore,
    vector_store: VectorStore,
):
    async def classify_node(state: BotState) -> BotState:
        result = await classify(state["user_message"], model_classifier)
        return {"intent": result}
