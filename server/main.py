import json
import os
import uuid
from aiohttp import web
from server.matcher import Matcher
from server.models import (
    offer_from_message,
    paired_message,
    ack_message,
    error_message,
    usage_update_message,
)
from server.pricing import is_known_model
from server.pricing import SUPPORTED_MODELS_BY_PROVIDER, get_supported_provider_models

matcher = Matcher()

# Maps offer_id -> peer's WebSocket so usage_report can be relayed
_peer_map: dict[str, web.WebSocketResponse] = {}


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def provider_models_handler(request: web.Request) -> web.Response:
    provider = request.query.get("provider", "")
    if provider:
        if provider not in SUPPORTED_MODELS_BY_PROVIDER:
            return web.json_response(
                {"error": f"Unknown provider: {provider}"},
                status=404,
            )
        return web.json_response(
            {
                "provider": provider,
                "models": get_supported_provider_models(provider),
            }
        )
    return web.json_response({"providers": SUPPORTED_MODELS_BY_PROVIDER})


async def ws_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    await ws.send_json(error_message("Invalid JSON"))
                    continue

                msg_type = data.get("type")
                if msg_type == "register":
                    try:
                        input_tokens_offered = data.get("input_tokens_offered", 0)
                        output_tokens_offered = data.get("output_tokens_offered", 0)
                        advanced_mode = (
                            input_tokens_offered > 0 or output_tokens_offered > 0
                        )

                        provider = str(data.get("provider", ""))
                        model = str(data.get("model", ""))
                        want_provider = str(data.get("want_provider", ""))
                        want_model = str(data.get("want_model", ""))

                        provider_models = set(get_supported_provider_models(provider))
                        want_provider_models = set(
                            get_supported_provider_models(want_provider)
                        )

                        if not provider_models:
                            await ws.send_json(
                                error_message(f"Unknown provider: {provider}")
                            )
                            continue
                        if not want_provider_models:
                            await ws.send_json(
                                error_message(f"Unknown provider: {want_provider}")
                            )
                            continue
                        if model not in provider_models:
                            await ws.send_json(
                                error_message(
                                    f"Unsupported model for {provider}: {model}"
                                )
                            )
                            continue
                        if want_model not in want_provider_models:
                            await ws.send_json(
                                error_message(
                                    f"Unsupported model for {want_provider}: {want_model}"
                                )
                            )
                            continue
                        if data.get("tokens_offered", 0) <= 0:
                            await ws.send_json(
                                error_message("tokens_offered must be positive")
                            )
                            continue
                        if advanced_mode and (
                            input_tokens_offered <= 0 or output_tokens_offered <= 0
                        ):
                            await ws.send_json(
                                error_message(
                                    "input_tokens_offered and output_tokens_offered must both be positive in advanced mode"
                                )
                            )
                            continue

                        offer_id = uuid.uuid4().hex[:8]
                        offer = offer_from_message(data, ws, offer_id)
                        await ws.send_json(ack_message(offer_id))

                        pairing = await matcher.add_offer(offer)
                        if pairing:
                            a, b = pairing.offer_a, pairing.offer_b
                            _peer_map[a.offer_id] = b.ws
                            _peer_map[b.offer_id] = a.ws
                            await a.ws.send_json(
                                paired_message(
                                    a,
                                    b,
                                    temp_key=pairing.temp_key_b,
                                    proxy_key=pairing.temp_key_a,
                                    tokens_granted=pairing.tokens_b_serves,
                                    tokens_to_serve=pairing.tokens_a_serves,
                                    input_tokens_granted=pairing.input_tokens_b_serves,
                                    output_tokens_granted=pairing.output_tokens_b_serves,
                                    input_tokens_to_serve=pairing.input_tokens_a_serves,
                                    output_tokens_to_serve=pairing.output_tokens_a_serves,
                                )
                            )
                            await b.ws.send_json(
                                paired_message(
                                    b,
                                    a,
                                    temp_key=pairing.temp_key_a,
                                    proxy_key=pairing.temp_key_b,
                                    tokens_granted=pairing.tokens_a_serves,
                                    tokens_to_serve=pairing.tokens_b_serves,
                                    input_tokens_granted=pairing.input_tokens_a_serves,
                                    output_tokens_granted=pairing.output_tokens_a_serves,
                                    input_tokens_to_serve=pairing.input_tokens_b_serves,
                                    output_tokens_to_serve=pairing.output_tokens_b_serves,
                                )
                            )
                    except KeyError as e:
                        await ws.send_json(error_message(f"Missing field: {e}"))

                elif msg_type == "usage_report":
                    offer_id = data.get("offer_id", "")
                    tokens = data.get("tokens", 0)
                    input_tokens = data.get("input_tokens", 0)
                    output_tokens = data.get("output_tokens", 0)
                    peer_ws = _peer_map.get(offer_id)
                    if peer_ws and not peer_ws.closed:
                        await peer_ws.send_json(
                            usage_update_message(
                                tokens=tokens,
                                input_tokens=input_tokens,
                                output_tokens=output_tokens,
                            )
                        )

                else:
                    await ws.send_json(
                        error_message(f"Unknown message type: {msg_type}")
                    )
            elif msg.type in (
                web.WSMsgType.CLOSE,
                web.WSMsgType.CLOSING,
                web.WSMsgType.ERROR,
            ):
                break
    finally:
        await matcher.remove_by_ws(ws)
        stale = [oid for oid, pw in _peer_map.items() if pw is ws]
        for oid in stale:
            del _peer_map[oid]

    return ws


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health_handler)
    app.router.add_get("/providers/models", provider_models_handler)
    app.router.add_get("/ws", ws_handler)
    return app


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    web.run_app(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
