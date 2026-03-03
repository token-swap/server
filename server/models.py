from __future__ import annotations
from dataclasses import dataclass
from aiohttp import web


@dataclass
class Offer:
    offer_id: str
    provider: str  # "openai" | "anthropic" | "gemini"
    model: str
    tokens_offered: int
    want_provider: str
    want_model: str
    proxy_url: str
    ws: web.WebSocketResponse


def offer_from_message(msg: dict, ws: web.WebSocketResponse, offer_id: str) -> Offer:
    """Build Offer from parsed 'register' WS message. Reads: provider, model,
    tokens_offered, want_provider, want_model, proxy_url.
    Raises KeyError on missing fields."""
    return Offer(
        offer_id=offer_id,
        provider=msg["provider"],
        model=msg["model"],
        tokens_offered=msg["tokens_offered"],
        want_provider=msg["want_provider"],
        want_model=msg["want_model"],
        proxy_url=msg["proxy_url"],
        ws=ws,
    )


@dataclass
class Pairing:
    offer_a: Offer
    offer_b: Offer
    temp_key_a: str
    temp_key_b: str
    tokens_a_serves: int
    tokens_b_serves: int


def paired_message(
    offer: Offer,
    peer: Offer,
    temp_key: str,
    proxy_key: str,
    tokens_granted: int,
    tokens_to_serve: int,
) -> dict:
    return {
        "type": "paired",
        "offer_id": offer.offer_id,
        "temp_key": temp_key,
        "proxy_key": proxy_key,
        "peer_url": peer.proxy_url,
        "peer_provider": peer.provider,
        "peer_model": peer.model,
        "tokens_granted": tokens_granted,
        "tokens_to_serve": tokens_to_serve,
    }


def ack_message(offer_id: str) -> dict:
    return {"type": "ack", "offer_id": offer_id}


def error_message(text: str) -> dict:
    return {"type": "error", "message": text}
