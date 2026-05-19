import pytest

from storage import init_db, close_db


@pytest.fixture
async def db():
    conn = await init_db()
    yield conn
    await close_db(conn)
