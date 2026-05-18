from agent.workflows import Workflow
from models import PendingAction


CHAT_PROMPT = """
You are a friendly Meal Prep Assistant. Format for Telegram (`*bold*`, bullet points, ≤4096 chars).
"""


class ChatWorkflow(Workflow):
    async def run(self) -> tuple[str, PendingAction | None]:
        return (
            "👨‍🍳 I can help you plan meals and add recipes.\n"
            "To make a meal plan say: 'Plan my meals', 'What should I eat this week', 'Make me a meal plan'\n"
            "To save a recipe say: 'add this recipe https://url.to.recipe'\n"
        ), None
