from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.recipes import router as recipes_router
from storage import RecipeStore
from tests.factories import make_recipe

INGEST_KEY = "test-ingest-key"


@pytest.fixture
def mock_recipe_store():
    store = MagicMock(spec=RecipeStore)
    store.get_id_by_source_url = AsyncMock(return_value=None)
    store.create = AsyncMock(return_value=1)
    return store


@pytest.fixture
def client(mock_recipe_store, monkeypatch):
    monkeypatch.setenv("INGEST_API_KEY", INGEST_KEY)
    app = FastAPI()
    app.include_router(recipes_router)
    app.state.recipe_store = mock_recipe_store
    return TestClient(app)


def ingest_payload() -> dict:
    recipe = make_recipe(source_url="https://example.com/recipes/pasta")
    return recipe.model_dump(mode="json", exclude={"id", "created_at", "embedded"})


def auth(key: str = INGEST_KEY) -> dict:
    return {"Authorization": f"Bearer {key}"}


# ---------------------------------------------------------------------------
# auth
# ---------------------------------------------------------------------------


def test_ingest_unconfigured_key_returns_503(client, monkeypatch):
    # Without INGEST_API_KEY set, the endpoint must be disabled — not open.
    monkeypatch.delenv("INGEST_API_KEY")
    resp = client.post("/recipes/ingest", json=ingest_payload(), headers=auth())
    assert resp.status_code == 503


def test_ingest_missing_token_returns_401(client):
    resp = client.post("/recipes/ingest", json=ingest_payload())
    assert resp.status_code == 401


def test_ingest_wrong_token_returns_401(client):
    resp = client.post(
        "/recipes/ingest", json=ingest_payload(), headers=auth("wrong-key")
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# ingest
# ---------------------------------------------------------------------------


def test_ingest_new_recipe_creates(client, mock_recipe_store):
    resp = client.post("/recipes/ingest", json=ingest_payload(), headers=auth())
    assert resp.status_code == 200
    assert resp.json() == {"id": 1, "created": True}
    mock_recipe_store.create.assert_awaited_once()


def test_ingest_duplicate_source_url_skips(client, mock_recipe_store):
    # Idempotency: re-scraping a site must not duplicate recipes — the endpoint
    # skips URLs it has seen and reports created=False so the CLI counts skips.
    mock_recipe_store.get_id_by_source_url = AsyncMock(return_value=42)
    resp = client.post("/recipes/ingest", json=ingest_payload(), headers=auth())
    assert resp.status_code == 200
    assert resp.json() == {"id": 42, "created": False}
    mock_recipe_store.create.assert_not_awaited()


def test_ingest_missing_source_url_returns_422(client):
    # source_url is the dedup key; a payload without it must be rejected by
    # validation, never stored.
    payload = ingest_payload()
    del payload["source_url"]
    resp = client.post("/recipes/ingest", json=payload, headers=auth())
    assert resp.status_code == 422
