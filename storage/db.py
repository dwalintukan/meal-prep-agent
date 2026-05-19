import os
import asyncpg
from pathlib import Path
from yoyo import read_migrations, get_backend


async def init_db() -> asyncpg.connection.Connection:
    db_url = os.getenv("DATABASE_URL")
    apply_migrations(db_url)
    conn = await asyncpg.connect(db_url)
    return conn


def apply_migrations(db_url: str) -> None:
    """Synchronously apply migrations"""
    backend = get_backend(db_url)
    migrations = read_migrations(str(Path(__file__).parent.parent / "migrations"))
    with backend.lock():
        for migration in backend.to_apply(migrations):
            backend.apply_one(migration)


async def close_db(db: asyncpg.connection.Connection) -> None:
    await db.close()
