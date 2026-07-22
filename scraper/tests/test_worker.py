"""
Worker tests: the page state machine the dashboard reports on.

Each branch of _process_page must land the page in exactly one terminal
status — a page left 'fetching', or marked 'ingested' when nothing was sent,
makes the dashboard lie about what the crawl did.

The Job passed to _process_page is the real row from create_job, because the
LLM cap is enforced in SQL: a hand-built Job would let the two disagree.
"""

from pathlib import Path

import httpx
import pytest

from models import JobCreate
from worker import _process_page

FIXTURES = Path(__file__).parent / "fixtures"
RECIPE_HTML = (FIXTURES / "recipe_jsonld.html").read_text()
NON_RECIPE_HTML = (FIXTURES / "non_recipe.html").read_text()

# No JSON-LD, but the words the cheap pre-filter looks for — the only shape of
# page that should ever reach the LLM fallback.
PREFILTER_PASSING_HTML = """
<html><body>
  <h1>Grandma's Pancakes</h1>
  <h2>Ingredients</h2><ul><li>2 cups flour</li><li>1 egg</li></ul>
  <h2>Instructions</h2><ol><li>Mix.</li><li>Fry.</li></ol>
</body></html>
"""


class FakeRobots:
    def __init__(self, allowed: bool = True):
        self.allowed = allowed

    def can_fetch(self, user_agent: str, url: str) -> bool:
        return self.allowed


class FakeFetcher:
    def __init__(self, html: str | None = None, error: Exception | None = None):
        self.html = html
        self.error = error

    async def fetch(self, url: str) -> str:
        if self.error is not None:
            raise self.error
        return self.html


class FakeClient:
    def __init__(self, ingest_result=None, parse_result=None, error=None):
        self.ingest_result = ingest_result or {"id": 7, "created": True}
        self.parse_result = parse_result
        self.error = error
        self.ingest_calls: list[dict] = []
        self.parse_calls: list[tuple[str, str]] = []

    async def ingest(self, recipe: dict) -> dict:
        self.ingest_calls.append(recipe)
        if self.error is not None:
            raise self.error
        return self.ingest_result

    async def parse(self, url: str, page_text: str) -> dict | None:
        self.parse_calls.append((url, page_text))
        if self.error is not None:
            raise self.error
        return self.parse_result


@pytest.fixture
async def queued_page(store):
    """Create a job plus one claimed page, so transitions hit real SQL."""

    async def _make(**job_kwargs):
        job = await store.create_job(
            JobCreate(root_url="https://example.com", **job_kwargs)
        )
        await store.enqueue_urls(job.id, ["https://example.com/recipes/pancakes"])
        return job, await store.claim_next_page(job.id)

    return _make


async def run_page(store, job, claimed, fetcher, client, robots=None, bfs=False):
    await _process_page(
        store, job, bfs, robots or FakeRobots(), fetcher, client, claimed
    )
    return (await store.list_pages(job.id))[0]


# ---------------------------------------------------------------------------
# non-fetch outcomes
# ---------------------------------------------------------------------------


async def test_robots_disallowed_page_is_not_fetched(store, queued_page):
    # robots_blocked must be decided before the request goes out, or the
    # politeness guarantee is cosmetic.
    job, claimed = await queued_page()
    fetcher = FakeFetcher(error=AssertionError("must not fetch"))

    row = await run_page(
        store, job, claimed, fetcher, FakeClient(), robots=FakeRobots(allowed=False)
    )

    assert row.status == "robots_blocked"


async def test_fetch_failure_marks_page_failed_with_stage(store, queued_page):
    # The error text is what the dashboard shows; losing the stage prefix makes
    # a fetch failure indistinguishable from an ingest one.
    job, claimed = await queued_page()

    row = await run_page(
        store,
        job,
        claimed,
        FakeFetcher(error=httpx.ConnectError("refused")),
        FakeClient(),
    )

    assert row.status == "failed"
    assert row.error.startswith("fetch:")


async def test_page_without_jsonld_is_no_recipe(store, queued_page):
    # With llm_fallback off, a non-recipe page must cost nothing beyond the
    # fetch — no backend call at all.
    job, claimed = await queued_page()
    client = FakeClient()

    row = await run_page(store, job, claimed, FakeFetcher(NON_RECIPE_HTML), client)

    assert row.status == "no_recipe"
    assert client.parse_calls == []
    assert client.ingest_calls == []


# ---------------------------------------------------------------------------
# ingest outcomes
# ---------------------------------------------------------------------------


async def test_recipe_page_ingests_and_records_backend_id(store, queued_page):
    job, claimed = await queued_page()
    client = FakeClient(ingest_result={"id": 99, "created": True})

    row = await run_page(store, job, claimed, FakeFetcher(RECIPE_HTML), client)

    assert row.status == "ingested"
    assert row.recipe_name == "Classic Pancakes"
    assert row.recipe_id == 99


async def test_created_false_records_duplicate_not_ingested(store, queued_page):
    # created=False is the backend's dedup signal. Recording it as 'ingested'
    # would inflate the crawl's reported yield on every re-scrape.
    job, claimed = await queued_page()
    client = FakeClient(ingest_result={"id": 42, "created": False})

    row = await run_page(store, job, claimed, FakeFetcher(RECIPE_HTML), client)

    assert row.status == "duplicate"


async def test_ingest_failure_marks_page_failed_with_stage(store, queued_page):
    job, claimed = await queued_page()
    client = FakeClient(error=httpx.ConnectError("refused"))

    row = await run_page(store, job, claimed, FakeFetcher(RECIPE_HTML), client)

    assert row.status == "failed"
    assert row.error.startswith("ingest:")


async def test_dry_run_finds_recipe_without_sending_it(store, queued_page):
    # The whole point of --dry-run: see what a crawl would yield without
    # writing anything to the backend.
    job, claimed = await queued_page(dry_run=True)
    client = FakeClient()

    row = await run_page(store, job, claimed, FakeFetcher(RECIPE_HTML), client)

    assert row.status == "found"
    assert row.recipe_name == "Classic Pancakes"
    assert client.ingest_calls == []


# ---------------------------------------------------------------------------
# llm fallback
# ---------------------------------------------------------------------------


async def test_llm_fallback_parses_page_that_clears_prefilter(store, queued_page):
    job, claimed = await queued_page(llm_fallback=True, llm_cap=1)
    recipe = {"name": "Parsed Pancakes", "source_url": "https://example.com"}
    client = FakeClient(parse_result=recipe, ingest_result={"id": 5, "created": True})

    row = await run_page(
        store, job, claimed, FakeFetcher(PREFILTER_PASSING_HTML), client
    )

    assert row.status == "ingested"
    assert row.recipe_name == "Parsed Pancakes"
    assert (await store.get_job(job.id)).llm_used == 1


async def test_llm_fallback_skips_page_that_fails_prefilter(store, queued_page):
    # The pre-filter is what keeps the cap from being burned on About pages
    # that could never parse as a recipe anyway.
    job, claimed = await queued_page(llm_fallback=True, llm_cap=1)
    client = FakeClient(parse_result={"name": "should not happen"})

    row = await run_page(store, job, claimed, FakeFetcher(NON_RECIPE_HTML), client)

    assert client.parse_calls == []
    assert row.status == "no_recipe"
    assert (await store.get_job(job.id)).llm_used == 0


async def test_llm_fallback_stops_at_cap(store, queued_page):
    # Once the cap is spent the page falls through to no_recipe rather than
    # retrying — the cap is a hard spend ceiling, not a soft target.
    job, claimed = await queued_page(llm_fallback=True, llm_cap=1)
    assert await store.try_use_llm(job.id) is True  # cap now exhausted
    client = FakeClient(parse_result={"name": "should not happen"})

    row = await run_page(
        store, job, claimed, FakeFetcher(PREFILTER_PASSING_HTML), client
    )

    assert client.parse_calls == []
    assert row.status == "no_recipe"


async def test_llm_fallback_not_used_when_jsonld_succeeds(store, queued_page):
    # JSON-LD is free and deterministic; spending an LLM call on a page that
    # already parsed is pure waste.
    job, claimed = await queued_page(llm_fallback=True)
    client = FakeClient()

    await run_page(store, job, claimed, FakeFetcher(RECIPE_HTML), client)

    assert client.parse_calls == []
    assert (await store.get_job(job.id)).llm_used == 0


async def test_llm_parse_failure_marks_page_failed_with_stage(store, queued_page):
    job, claimed = await queued_page(llm_fallback=True, llm_cap=1)
    client = FakeClient(error=httpx.ConnectError("backend down"))

    row = await run_page(
        store, job, claimed, FakeFetcher(PREFILTER_PASSING_HTML), client
    )

    assert row.status == "failed"
    assert row.error.startswith("llm parse:")
