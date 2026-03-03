import json
import os
import uuid
from aiohttp import web
from server.matcher import Matcher
from server.models import offer_from_message, paired_message, ack_message, error_message
from server.pricing import is_known_model

matcher = Matcher()


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


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
                        if not is_known_model(data.get("model", "")):
                            await ws.send_json(
                                error_message(f"Unknown model: {data.get('model')}")
                            )
                            continue
                        if not is_known_model(data.get("want_model", "")):
                            await ws.send_json(
                                error_message(
                                    f"Unknown model: {data.get('want_model')}"
                                )
                            )
                            continue
                        if data.get("tokens_offered", 0) <= 0:
                            await ws.send_json(
                                error_message("tokens_offered must be positive")
                            )
                            continue

                        offer_id = uuid.uuid4().hex[:8]
                        offer = offer_from_message(data, ws, offer_id)
                        await ws.send_json(ack_message(offer_id))

                        pairing = await matcher.add_offer(offer)
                        if pairing:
                            a, b = pairing.offer_a, pairing.offer_b
                            await a.ws.send_json(
                                paired_message(
                                    a,
                                    b,
                                    temp_key=pairing.temp_key_b,
                                    proxy_key=pairing.temp_key_a,
                                    tokens_granted=pairing.tokens_b_serves,
                                    tokens_to_serve=pairing.tokens_a_serves,
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
                                )
                            )
                    except KeyError as e:
                        await ws.send_json(error_message(f"Missing field: {e}"))
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

    return ws


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health_handler)
    app.router.add_get("/ws", ws_handler)
    return app


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    web.run_app(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
