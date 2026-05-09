from datetime import datetime
from anthropic import AsyncAnthropic

from agent.prompts import PARSE_RECIPE_PROMPT
from agent.tools import PARSE_RECIPE_TOOL
from models import Recipe
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

        self.recipe: Recipe | None = None

    async def _parse_url(self) -> None:
        # Call LLM to parse
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
                    "content": self.url,
                }
            ],
        )

        # Parse outputs
        input = resp.content[0].input
        recipe = {
            "name": input["name"],
            "instructions": input["instructions"],
            "ingredients": input["ingredients"],
            "servings": input["servings"],
            "prep_minutes": input["prep_minutes"],
            "cook_minutes": input["cook_minutes"],
            "tags": input["tags"],
            "created_at": datetime.today(),
        }

        # Validate all fields present
        for key, val in recipe.items():
            if val is None:
                raise ValueError(f"Parsed recipe could not find: {key}")

        self.recipe = recipe

    async def run(self) -> str:
        try:
            self._parse_url()
        except ValueError:
            return f"Couldn't parse recipe from {self.url}"

        return ""
