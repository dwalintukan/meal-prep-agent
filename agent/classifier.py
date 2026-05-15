from enum import Enum
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

from agent.prompts import CLASSIFY_INTENT_PROMPT


class Intent(str, Enum):
    PLAN = "plan"
    PARSE_RECIPE = "parse_recipe"
    CHAT = "chat"


class ClassifiedIntent(BaseModel):
    intent: Intent = Field(description="Intent of the message")
    confidence: float = Field(
        description="Confidence of the classification from 0.0 to 1.0"
    )


async def classify(message: str, model: ChatAnthropic) -> ClassifiedIntent:
    classify_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=CLASSIFY_INTENT_PROMPT,
                additional_kwargs={"cache_control": {"type": "ephemeral"}},
            ),
            ("human", "Classify this message: {message}"),
        ]
    )
    chain = classify_prompt | model.with_structured_output(ClassifiedIntent)
    intent: ClassifiedIntent = await chain.ainvoke({"message": message})
    print(f"Intent: {intent.intent} {intent.confidence}")
    return intent
