import pytest

from agent.workflows.chat import ChatWorkflow


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def workflow():
    return ChatWorkflow()


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------


async def test_run_returns_string(workflow):
    result = await workflow.run()
    assert isinstance(result, str)


async def test_run_returns_nonempty_string(workflow):
    result = await workflow.run()
    assert len(result) > 0


async def test_run_mentions_plan_meals(workflow):
    result = await workflow.run()
    assert "plan" in result.lower()


async def test_run_mentions_add_recipe(workflow):
    result = await workflow.run()
    assert "add" in result.lower() or "recipe" in result.lower()


async def test_run_is_idempotent(workflow):
    first = await workflow.run()
    second = await workflow.run()
    assert first == second


async def test_run_requires_no_arguments():
    wf = ChatWorkflow()
    result = await wf.run()
    assert isinstance(result, str)
