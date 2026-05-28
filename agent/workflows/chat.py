from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from storage import PromptStore
from models import PromptType


class ChatInput(BaseModel):
    reply: str = Field(description="LLM reply from the model")


class ChatWorkflow:
    def __init__(self, message: str, model: BaseChatModel, prompt_store: PromptStore):
        self.message = message
        self.model = model
        self.prompt_store = prompt_store

    async def run(self) -> str:
        prompt = await self.prompt_store.get(PromptType.CHAT)
        sys_msg = SystemMessage(
            content=prompt.prompt,
            additional_kwargs={"cache_control": {"type": "ephemeral"}},
        )
        human_msg = HumanMessage(content=self.message)
        messages = [sys_msg, human_msg]

        resp = await self.model.with_structured_output(ChatInput).ainvoke(messages)

        return resp
