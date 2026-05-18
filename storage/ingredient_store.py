from typing import Protocol

import aiosqlite
from models.domain import Ingredient
from storage.db import transaction


class IIngredientStore(Protocol):
    async def create(self, ingredient: Ingredient, recipe_id: int) -> int: ...
    async def get(self, id: int) -> Ingredient | None: ...
    async def get_all(self) -> list[Ingredient]: ...
    async def update(self, ingredient: Ingredient) -> None: ...
    async def delete(self, id: int) -> None: ...


class IngredientStore:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self, ingredient: Ingredient, recipe_id: int) -> int:
        async with transaction(self.db):
            async with self.db.execute(
                "INSERT INTO ingredients (recipe_id, name, unit, amount) VALUES (?, ?, ?, ?)",
                (
                    recipe_id,
                    ingredient.name,
                    ingredient.unit,
                    ingredient.amount,
                ),
            ) as cur:
                ingredient_id = cur.lastrowid
            if ingredient_id is None:
                raise RuntimeError("INSERT into ingredients returned no rowid")

            print(
                f"Ingredient created: recipe_id={recipe_id} id={ingredient_id} name={ingredient.name}"
            )

            return ingredient_id

    async def get(self, id: int) -> Ingredient | None:
        async with self.db.execute(
            "SELECT * FROM ingredients WHERE id = ?", (id,)
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return None
        return self._parse_ingredient(row)

    async def get_all(self) -> list[Ingredient]:
        async with self.db.execute("SELECT * FROM ingredients") as cur:
            rows = await cur.fetchall()
        return [self._parse_ingredient(r) for r in rows]

    async def update(self, ingredient: Ingredient) -> None:
        async with transaction(self.db):
            await self.db.execute(
                "UPDATE ingredients SET name=?, unit=?, amount=? WHERE id=?",
                (ingredient.name, ingredient.unit, ingredient.amount, ingredient.id),
            )

    async def delete(self, id: int) -> None:
        async with transaction(self.db):
            await self.db.execute("DELETE FROM ingredients WHERE id = ?", (id,))

    def _parse_ingredient(self, row: dict) -> Ingredient:
        return Ingredient(
            id=row["id"], name=row["name"], unit=row["unit"], amount=row["amount"]
        )
