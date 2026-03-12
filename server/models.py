from __future__ import annotations
from dataclasses import dataclass
from typing import cast
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
    input_tokens_offered: int = 0
    output_tokens_offered: int = 0

    @property
    def advanced(self) -> bool:
        return self.input_tokens_offered > 0 or self.output_tokens_offered > 0


def offer_from_message(
    msg: dict[str, object], ws: web.WebSocketResponse, offer_id: str
) -> Offer:
    """Build Offer from parsed 'register' WS message. Reads: provider, model,
    tokens_offered, want_provider, want_model, proxy_url.
    Raises KeyError on missing fields."""
    return Offer(
        offer_id=offer_id,
        provider=str(msg["provider"]),
        model=str(msg["model"]),
        tokens_offered=int(cast(int | str, msg["tokens_offered"])),
        want_provider=str(msg["want_provider"]),
        want_model=str(msg["want_model"]),
        proxy_url=str(msg["proxy_url"]),
        ws=ws,
        input_tokens_offered=int(cast(int | str, msg.get("input_tokens_offered", 0))),
        output_tokens_offered=int(cast(int | str, msg.get("output_tokens_offered", 0))),
    )


@dataclass
class Pairing:
    offer_a: Offer
    offer_b: Offer
    temp_key_a: str
    temp_key_b: str
    tokens_a_serves: int
    tokens_b_serves: int
    input_tokens_a_serves: int = 0
    output_tokens_a_serves: int = 0
    input_tokens_b_serves: int = 0
    output_tokens_b_serves: int = 0


def paired_message(
    offer: Offer,
    peer: Offer,
    temp_key: str,
    proxy_key: str,
    tokens_granted: int,
    tokens_to_serve: int,
    input_tokens_granted: int = 0,
    output_tokens_granted: int = 0,
    input_tokens_to_serve: int = 0,
    output_tokens_to_serve: int = 0,
) -> dict[str, object]:
    msg: dict[str, object] = {
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
    if input_tokens_granted:
        msg["input_tokens_granted"] = input_tokens_granted
    if output_tokens_granted:
        msg["output_tokens_granted"] = output_tokens_granted
    if input_tokens_to_serve:
        msg["input_tokens_to_serve"] = input_tokens_to_serve
    if output_tokens_to_serve:
        msg["output_tokens_to_serve"] = output_tokens_to_serve
    return msg


def ack_message(offer_id: str) -> dict[str, str]:
    return {"type": "ack", "offer_id": offer_id}


def error_message(text: str) -> dict[str, str]:
    return {"type": "error", "message": text}


def usage_update_message(
    tokens: int = 0, input_tokens: int = 0, output_tokens: int = 0
) -> dict[str, object]:
    msg: dict[str, object] = {"type": "usage_update", "tokens": tokens}
    if input_tokens:
        msg["input_tokens"] = input_tokens
    if output_tokens:
        msg["output_tokens"] = output_tokens
    return msg


def unpaired_message() -> dict[str, str]:
    return {"type": "unpaired"}
