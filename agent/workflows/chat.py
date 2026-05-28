from storage import PromptStore
from models import PromptType


class ChatWorkflow:
    def __init__(self, prompt_store: PromptStore):
        self.prompt_store = prompt_store

    async def run(self) -> str:
        prompt = await self.prompt_store.get(PromptType.CHAT)
        return prompt
