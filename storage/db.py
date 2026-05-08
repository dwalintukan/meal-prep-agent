from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator
import aiosqlite
from pathlib import Path
from yoyo import read_migrations, get_backend


async def init_db(path: str) -> aiosqlite.Connection:
    # Apply migrations
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    apply_migrations(path)

    # Connect to DB
    db = await aiosqlite.connect(path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys = ON")

    return db


# Synchronously apply migrations
def apply_migrations(db_path: str) -> None:
    backend = get_backend(f"sqlite:///{db_path}")
    migrations = read_migrations(str(Path(__file__).parent.parent / "migrations"))
    with backend.lock():
        for migration in backend.to_apply(migrations):
            backend.apply_one(migration)


@asynccontextmanager
async def transaction(db: aiosqlite.Connection) -> AsyncGenerator[Any, Any]:
    await db.execute("BEGIN")
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise


async def close_db(db: aiosqlite.Connection) -> None:
    await db.close()
