import pytest
import pytest_asyncio
from server.main import create_app


@pytest_asyncio.fixture
async def client(aiohttp_client):
    return await aiohttp_client(create_app())


@pytest.mark.asyncio
async def test_unknown_provider_returns_404(client):
    resp = await client.get("/providers/models?provider=unknown_provider")
    assert resp.status == 404
    body = await resp.json()
    assert "error" in body
    assert "unknown_provider" in body["error"]


@pytest.mark.asyncio
async def test_known_provider_returns_200(client):
    resp = await client.get("/providers/models?provider=openai")
    assert resp.status == 200
    body = await resp.json()
    assert body["provider"] == "openai"
    assert isinstance(body["models"], list)
    assert len(body["models"]) > 0


@pytest.mark.asyncio
async def test_no_provider_returns_all_providers(client):
    resp = await client.get("/providers/models")
    assert resp.status == 200
    body = await resp.json()
    assert "providers" in body
    assert "openai" in body["providers"]
