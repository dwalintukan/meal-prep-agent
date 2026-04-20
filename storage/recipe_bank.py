from models import Recipe


class RecipeBank:
    async def load_all(self) -> dict[int, Recipe]:
        pass

    async def get(self, recipe_id: int) -> Recipe | None:
        pass

    async def exists(self, recipe_id: int) -> bool:
        pass

    async def save(self, recipe: Recipe) -> None:
        pass
