from storage import init_db, close_db

# ---------------------------------------------------------------------------
# init_db
# ---------------------------------------------------------------------------


async def test_init_db_creates_file(tmp_path):
    path = tmp_path / "test.db"
    await init_db(str(path))
    assert path.exists()


async def test_init_db_creates_parent_dirs(tmp_path):
    path = tmp_path / "nested" / "deep" / "test.db"
    await init_db(str(path))
    assert path.exists()


# ---------------------------------------------------------------------------
# close_db
# ---------------------------------------------------------------------------


async def test_close_db(tmp_path):
    db = await init_db(str(tmp_path / "test.db"))
    await close_db(db)
    assert db._connection is None


# ---------------------------------------------------------------------------
# apply_migrations
# ---------------------------------------------------------------------------


async def test_migrations_create_tables(tmp_path):
    db = await init_db(str(tmp_path / "test.db"))
    async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cur:
        tables = {row["name"] for row in await cur.fetchall()}
    assert {"recipes", "ingredients", "weekly_plans", "shopping_items"}.issubset(tables)


async def test_migrations_idempotent(tmp_path):
    from storage.db import apply_migrations

    path = str(tmp_path / "test.db")
    apply_migrations(path)
    apply_migrations(path)  # second call should not raise
