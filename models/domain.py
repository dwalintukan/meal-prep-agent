from pydantic import BaseModel
from datetime import datetime


class Ingredient(BaseModel):
    id: int
    name: str
    unit: str
    amount: float


class Recipe(BaseModel):
    id: int
    name: str
    instructions: list[str]
    ingredients: list[Ingredient]
    servings: int
    prep_minutes: int
    cook_minutes: int
    tags: list[str]
    created_at: datetime
