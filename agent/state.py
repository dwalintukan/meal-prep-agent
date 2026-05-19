from typing import TypedDict

from agent.classifier import Intent
from models import Recipe


class BotState(TypedDict):
    chat_id: int
    user_message: str
    intent: Intent | None
    reply: str | None
    pending_recipe: Recipe | None
