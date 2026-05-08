import json
from datetime import datetime, date
from typing import Protocol
import aiosqlite

from models import WeeklyPlan
import utils.date


class IWeeklyPlanStore(Protocol):
    async def create(self, plan: WeeklyPlan) -> None: ...
    async def get(self, id: int) -> WeeklyPlan | None: ...
    async def get_all(self) -> list[WeeklyPlan]: ...
    async def update(self, plan: WeeklyPlan) -> None: ...
    async def delete(self, id: int) -> None: ...


class WeeklyPlanStore:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self, plan: WeeklyPlan, commit: bool = True) -> int:
        cur = await self.db.execute(
            "INSERT INTO weekly_plans (timestamp, recipe_ids, created_at) VALUES (?, ?, ?)",
            (
                plan.timestamp.isoformat(),
                json.dumps(plan.recipe_ids),
                plan.created_at.isoformat(),
            ),
        )
        if commit:
            await self.db.commit()
        return cur.lastrowid

    async def get(self, id: int) -> WeeklyPlan | None:
        async with self.db.execute(
            "SELECT * FROM weekly_plans WHERE id = ?", (id,)
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return None
        return self._row_to_plan(row)

    async def get_last_weekly_plan_recipe_ids(self) -> WeeklyPlan | None:
        last_monday = utils.date.last_monday()

        async with self.db.execute(
            "SELECT * FROM weekly_plans WHERE timestamp = ? LIMIT 1",
            (last_monday.isoformat(),),
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return None
        return self._row_to_plan(row)

    async def get_all(self) -> list[WeeklyPlan]:
        async with self.db.execute("SELECT * FROM weekly_plans") as cur:
            rows = await cur.fetchall()
        return [self._row_to_plan(row) for row in rows]

    async def update(self, plan: WeeklyPlan) -> None:
        await self.db.execute(
            "UPDATE weekly_plans SET timestamp=?, recipe_ids=?, created_at=? WHERE id=?",
            (
                plan.timestamp.isoformat(),
                json.dumps(plan.recipe_ids),
                plan.created_at.isoformat(),
                plan.id,
            ),
        )
        await self.db.commit()

    async def delete(self, id: int) -> None:
        await self.db.execute("DELETE FROM weekly_plans WHERE id = ?", (id,))
        await self.db.commit()

    @staticmethod
    def _row_to_plan(row) -> WeeklyPlan:
        return WeeklyPlan(
            id=row["id"],
            timestamp=date.fromisoformat(row["timestamp"]),
            recipe_ids=json.loads(row["recipe_ids"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
