import pytest
from dotenv import load_dotenv

from store import ScrapeStore, init_pool

load_dotenv()


@pytest.fixture
async def store():
    """
    A ScrapeStore against a real Postgres — these tests exist to verify SQL
    semantics (SKIP LOCKED, ON CONFLICT, atomic counter updates) that a fake
    store would define away.
    """
    pool = await init_pool()
    scrape_store = ScrapeStore(pool)
    await scrape_store.bootstrap()
    # jobs cascades to pages via the FK.
    await pool.execute("TRUNCATE scraper.jobs RESTART IDENTITY CASCADE")
    yield scrape_store
    await pool.close()
