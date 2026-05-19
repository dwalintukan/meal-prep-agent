from typing import TypedDict

from agent.classifier import ClassifiedIntent
from models import Recipe


class BotState(TypedDict):
    chat_id: int
    user_message: str
    intent: ClassifiedIntent | None
    reply: str | None
    pending_recipe: Recipe | None
