import pytest
import pytest_asyncio
from server.main import create_app


@pytest_asyncio.fixture
async def client(aiohttp_client):
    return await aiohttp_client(create_app())


@pytest.mark.asyncio
async def test_exchange_estimate_returns_simple_quote(client):
    resp = await client.get(
        "/exchange/estimate?offered_provider=openai"
        "&offered_model=gpt-4.1"
        "&wanted_provider=anthropic"
        "&wanted_model=claude-opus-4-6"
        "&offered_tokens=10000"
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["mode"] == "simple"
    assert isinstance(body["estimated_received_tokens"], int)
    assert body["estimated_received_tokens"] > 0
    assert isinstance(body["rate"], float)


@pytest.mark.asyncio
async def test_exchange_estimate_returns_advanced_quote(client):
    resp = await client.get(
        "/exchange/estimate?offered_provider=openai"
        "&offered_model=gpt-4.1"
        "&wanted_provider=anthropic"
        "&wanted_model=claude-opus-4-6"
        "&offered_input_tokens=7000"
        "&offered_output_tokens=3000"
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["mode"] == "advanced"
    assert body["estimated_input_received_tokens"] > 0
    assert body["estimated_output_received_tokens"] > 0
    assert body["estimated_received_tokens"] == (
        body["estimated_input_received_tokens"]
        + body["estimated_output_received_tokens"]
    )


@pytest.mark.asyncio
async def test_exchange_estimate_requires_offer_amount(client):
    resp = await client.get(
        "/exchange/estimate?offered_provider=openai"
        "&offered_model=gpt-4.1"
        "&wanted_provider=anthropic"
        "&wanted_model=claude-opus-4-6"
    )
    assert resp.status == 400
    body = await resp.json()
    assert "error" in body


@pytest.mark.asyncio
async def test_exchange_estimate_rejects_unknown_provider(client):
    resp = await client.get(
        "/exchange/estimate?offered_provider=unknown"
        "&offered_model=gpt-4.1"
        "&wanted_provider=anthropic"
        "&wanted_model=claude-opus-4-6"
        "&offered_tokens=10000"
    )
    assert resp.status == 404
    body = await resp.json()
    assert "error" in body
