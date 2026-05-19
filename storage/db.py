import os
import asyncpg
from pathlib import Path
from yoyo import read_migrations, get_backend


async def init_db() -> asyncpg.connection.Connection:
    apply_migrations()
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    return conn


def apply_migrations() -> None:
    """Synchronously apply migrations"""
    backend = get_backend(os.getenv("DATABASE_URL"))
    migrations = read_migrations(str(Path(__file__).parent.parent / "migrations"))
    with backend.lock():
        for migration in backend.to_apply(migrations):
            backend.apply_one(migration)


async def close_db(db: asyncpg.connection.Connection) -> None:
    await db.close()
