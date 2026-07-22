"""
Store tests: the invariants the crawl's correctness rests on.

Everything here is concurrency- or SQL-semantics-sensitive, which is why it
runs against a real Postgres rather than a fake.
"""

import asyncio

from models import JobCreate


async def make_job(store, **overrides) -> int:
    defaults = dict(root_url="https://example.com", max_pages=500, llm_cap=20)
    defaults.update(overrides)
    job = await store.create_job(JobCreate(**defaults))
    return job.id


# ---------------------------------------------------------------------------
# llm cap
# ---------------------------------------------------------------------------


async def test_try_use_llm_cap_holds_under_concurrency(store):
    # The cap is the only thing bounding LLM spend on a crawl. Slots call this
    # in parallel, so a read-then-write would let them all pass the same check
    # and overspend; the UPDATE ... WHERE llm_used < llm_cap must be atomic.
    job_id = await make_job(store, llm_cap=20)

    results = await asyncio.gather(*(store.try_use_llm(job_id) for _ in range(50)))

    assert sum(results) == 20
    job = await store.get_job(job_id)
    assert job.llm_used == 20


async def test_try_use_llm_refuses_past_cap(store):
    job_id = await make_job(store, llm_cap=1)
    assert await store.try_use_llm(job_id) is True
    assert await store.try_use_llm(job_id) is False


# ---------------------------------------------------------------------------
# page frontier
# ---------------------------------------------------------------------------


async def test_claim_next_page_never_serves_the_same_page_twice(store):
    # Two crawl slots claiming in parallel must get disjoint pages, or the same
    # URL gets fetched twice and ingested twice.
    job_id = await make_job(store)
    await store.enqueue_urls(job_id, [f"https://example.com/{i}" for i in range(10)])

    claims = await asyncio.gather(*(store.claim_next_page(job_id) for _ in range(10)))

    ids = [c["id"] for c in claims if c is not None]
    assert len(ids) == 10
    assert len(set(ids)) == 10


async def test_claim_next_page_returns_none_when_frontier_empty(store):
    job_id = await make_job(store)
    assert await store.claim_next_page(job_id) is None


async def test_enqueue_urls_dedups(store):
    # The (job_id, url) unique constraint is the persistent "seen" set. Without
    # it a BFS crawl re-enqueues every link it re-encounters and never ends.
    job_id = await make_job(store)
    urls = ["https://example.com/a", "https://example.com/b"]

    assert await store.enqueue_urls(job_id, urls) == 2
    assert await store.enqueue_urls(job_id, urls) == 0
    assert await store.count_pages(job_id) == 2


async def test_enqueue_urls_is_per_job(store):
    # Two jobs crawling the same site must not share a frontier.
    first = await make_job(store)
    second = await make_job(store)
    url = ["https://example.com/a"]

    assert await store.enqueue_urls(first, url) == 1
    assert await store.enqueue_urls(second, url) == 1


# ---------------------------------------------------------------------------
# terminal transitions
# ---------------------------------------------------------------------------


async def test_finish_job_skips_leftover_queued_pages(store):
    # A finished job must leave nothing 'queued', or the dashboard shows work
    # pending on a job the worker will never touch again.
    job_id = await make_job(store)
    await store.enqueue_urls(job_id, ["https://example.com/a", "https://example.com/b"])
    claimed = await store.claim_next_page(job_id)
    await store.finish_page(claimed["id"], "ingested")

    await store.finish_job(job_id, "done")

    counts = await store.job_counts(job_id)
    assert counts == {"ingested": 1, "skipped": 1}


async def test_retry_failed_requeues_pages_and_reopens_job(store):
    # Retry has to do both halves: requeueing pages under a job left 'done'
    # would strand them, since the worker only claims pending/running jobs.
    job_id = await make_job(store)
    await store.enqueue_urls(job_id, ["https://example.com/a", "https://example.com/b"])
    first = await store.claim_next_page(job_id)
    await store.finish_page(first["id"], "failed", error="boom")
    await store.finish_job(job_id, "done")

    requeued = await store.retry_failed(job_id)

    assert requeued == 2  # the failed page plus the one skipped by finish_job
    job = await store.get_job(job_id)
    assert job.status == "pending"
    assert job.counts == {"queued": 2}


async def test_retry_failed_clears_stale_errors(store):
    # A requeued page keeps its old error otherwise, so a page that succeeds on
    # retry still reads as failed in the dashboard.
    job_id = await make_job(store)
    await store.enqueue_urls(job_id, ["https://example.com/a"])
    page = await store.claim_next_page(job_id)
    await store.finish_page(page["id"], "failed", error="boom")

    await store.retry_failed(job_id)

    assert (await store.list_pages(job_id))[0].error is None


async def test_cancel_job_refuses_terminal_jobs(store):
    # Cancelling a finished job would rewrite its status and finished_at,
    # losing the record of how it actually ended.
    job_id = await make_job(store)
    await store.finish_job(job_id, "done")
    assert await store.cancel_job(job_id) is None


# ---------------------------------------------------------------------------
# restart recovery
# ---------------------------------------------------------------------------


async def test_requeue_stuck_fetching_returns_orphaned_pages(store):
    # A crash mid-fetch leaves pages in 'fetching' with nobody working them.
    # Without this they are never reclaimed and the crawl silently loses them.
    job_id = await make_job(store)
    await store.enqueue_urls(job_id, ["https://example.com/a"])
    await store.claim_next_page(job_id)
    assert await store.job_counts(job_id) == {"fetching": 1}

    assert await store.requeue_stuck_fetching() == 1

    assert await store.job_counts(job_id) == {"queued": 1}


async def test_claim_next_job_reclaims_running_job(store):
    # Restart resume: a job left 'running' by a crash must be re-claimable, or
    # it stalls forever with a durable frontier nobody drains.
    job_id = await make_job(store)
    assert (await store.claim_next_job()).id == job_id
    assert (await store.claim_next_job()).id == job_id


async def test_claim_next_job_skips_terminal_jobs(store):
    job_id = await make_job(store)
    await store.finish_job(job_id, "done")
    assert await store.claim_next_job() is None
