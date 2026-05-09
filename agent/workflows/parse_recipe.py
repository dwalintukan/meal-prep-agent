from anthropic import AsyncAnthropic

from agent.prompts import PARSE_RECIPE_PROMPT
from storage import RecipeStore, IngredientStore


class ParseRecipeWorkflow:
    def __init__(
        self,
        client: AsyncAnthropic,
        recipe_store: RecipeStore,
        ingredient_store: IngredientStore,
        url: str,
    ):
        self.client = client
        self.recipe_store = recipe_store
        self.ingredient_store = ingredient_store
        self.url = url

    async def _parse_url(self):
        resp = await self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=[
                {
                    "type": "text",
                    "text": PARSE_RECIPE_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=[PARSE_RECIPE_TOOL],
            tool_choice={"type": "tool", "name": "create_meal_plan"},
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ],
        )

    async def run(self) -> str:
        pass
