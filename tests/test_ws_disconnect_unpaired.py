import asyncio

import pytest

from server.main import create_app


@pytest.mark.asyncio
async def test_disconnect_notifies_peer_with_unpaired(aiohttp_client):
    client = await aiohttp_client(create_app())
    ws_a = await client.ws_connect("/ws")
    ws_b = await client.ws_connect("/ws")

    await ws_a.send_json(
        {
            "type": "register",
            "provider": "openai",
            "model": "gpt-5.2",
            "tokens_offered": 1000,
            "want_provider": "anthropic",
            "want_model": "claude-sonnet-4-6",
            "proxy_url": "https://a.example.com",
        }
    )
    ack_a = await ws_a.receive_json()
    assert ack_a["type"] == "ack"

    await ws_b.send_json(
        {
            "type": "register",
            "provider": "anthropic",
            "model": "claude-sonnet-4-6",
            "tokens_offered": 1000,
            "want_provider": "openai",
            "want_model": "gpt-5.2",
            "proxy_url": "https://b.example.com",
        }
    )
    ack_b = await ws_b.receive_json()
    assert ack_b["type"] == "ack"

    paired_a = await ws_a.receive_json()
    paired_b = await ws_b.receive_json()
    assert paired_a["type"] == "paired"
    assert paired_b["type"] == "paired"

    await ws_a.close()

    unpaired = await asyncio.wait_for(ws_b.receive_json(), timeout=1.0)
    assert unpaired["type"] == "unpaired"

    await ws_b.close()
