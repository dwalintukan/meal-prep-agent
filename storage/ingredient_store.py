import asyncpg

from models.domain import Ingredient


class IngredientStore:
    def __init__(self, db: asyncpg.connection.Connection):
        self.db = db

    async def create(self, ingredient: Ingredient, recipe_id: int) -> int:
        async with self.db.transaction():
            ingredient_id = await self.db.fetchval(
                "INSERT INTO ingredients (recipe_id, name, unit, amount) "
                "VALUES ($1, $2, $3, $4) "
                "RETURNING id",
                recipe_id,
                ingredient.name,
                ingredient.unit,
                ingredient.amount,
            )
            if ingredient_id is None:
                raise RuntimeError("INSERT into ingredients returned no rowid")

            print(
                f"Ingredient created: recipe_id={recipe_id} id={ingredient_id} name={ingredient.name}"
            )

            return ingredient_id

    async def get(self, id: int) -> Ingredient | None:
        row = await self.db.fetchrow("SELECT * FROM ingredients WHERE id = $1", id)
        if row is None:
            return None
        return self._parse_ingredient(row)

    async def get_all(self) -> list[Ingredient]:
        rows = await self.db.fetch("SELECT * FROM ingredients")
        return [self._parse_ingredient(r) for r in rows]

    async def update(self, ingredient: Ingredient) -> None:
        async with self.db.transaction():
            await self.db.execute(
                "UPDATE ingredients SET name=$1, unit=$2, amount=$3 WHERE id=$4",
                ingredient.name,
                ingredient.unit,
                ingredient.amount,
                ingredient.id,
            )

    async def delete(self, id: int) -> None:
        async with self.db.transaction():
            await self.db.execute("DELETE FROM ingredients WHERE id = $1", id)

    def _parse_ingredient(self, row) -> Ingredient:
        return Ingredient(
            id=row["id"], name=row["name"], unit=row["unit"], amount=row["amount"]
        )
