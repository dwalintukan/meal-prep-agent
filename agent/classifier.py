from enum import Enum
from pydantic import BaseModel
from anthropic import AsyncAnthropic

from agent.prompts import CLASSIFY_INTENT_PROMPT
from agent.tools import CLASSIFY_INTENT_TOOL


class Intent(str, Enum):
    PLAN = "plan"
    CHAT = "chat"


class ClassifiedIntent(BaseModel):
    intent: Intent
    confidence: float


async def classify(message: str, client: AsyncAnthropic) -> ClassifiedIntent:
    message = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=64,
        system=[{"type": "text", "text": CLASSIFY_INTENT_PROMPT}],
        tools=[CLASSIFY_INTENT_TOOL],
        tool_choice={"type": "tool", "name": "classify_intent"},
        messages=[
            {
                "role": "user",
                "content": f"Classify this mesage: {message}",
            }
        ],
    )
