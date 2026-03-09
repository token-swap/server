# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-03
**Commit:** b1d77d3
**Branch:** master

## OVERVIEW

WebSocket-based LLM token exchange server. Users offer tokens from one AI provider and receive tokens from another, with pricing based on market rates. Built with Python 3.11+ / aiohttp.

## STRUCTURE

```
.
├── pyproject.toml        # Package metadata, sole dependency: aiohttp
├── Dockerfile            # Multi-stage build, runs as non-root
├── .dockerignore         # Keeps build context clean
└── server/               # Single Python package
    ├── __init__.py        # Empty package marker
    ├── main.py            # aiohttp app, WS handler, routes, entrypoint
    ├── matcher.py         # In-memory offer matching engine
    ├── models.py          # Offer/Pairing dataclasses, message builders
    └── pricing.py         # Model pricing table, exchange rate calculator
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Add a new AI model | `server/pricing.py` | Add entry to `PRICING` dict |
| Change matching logic | `server/matcher.py` | `Matcher.add_offer()` does complementary matching |
| Add WS message types | `server/main.py` | `ws_handler` switch on `msg_type` |
| Add REST endpoints | `server/main.py` | `create_app()` registers routes |
| Modify WS message format | `server/models.py` | `paired_message()`, `ack_message()`, `error_message()` |
| Change exchange math | `server/pricing.py` | `calculate_exchange()` uses `avg_price()` ratio |

## CONVENTIONS

- **Dataclasses over dicts** for domain objects (`Offer`, `Pairing`)
- **Message builders** are plain functions returning dicts, not methods on dataclasses
- **No ORM / no persistence** — all state is in-memory (`Matcher._offers` list)
- **asyncio.Lock** for concurrency safety in `Matcher`
- **Type hints** on all function signatures
- **Env vars** for config: `HOST` (default `0.0.0.0`), `PORT` (default `8080`)
- **HARD RULE**: After any code or configuration change, run tests to verify (`python -m pytest -q`) before considering the task complete

## ANTI-PATTERNS (THIS PROJECT)

- Do NOT add persistence without rethinking `Matcher` — it assumes single-process in-memory state
- Do NOT reference `Offer.ws` outside WS handler lifecycle — the WebSocketResponse is tied to the connection
- `PRICING` dict keys are the canonical model identifiers — do NOT use display names or aliases

## DATA FLOW

```
Client WS connect -> /ws
  -> send {"type": "register", provider, model, tokens_offered, want_provider, want_model, proxy_url}
  <- {"type": "ack", offer_id}
  <- (if match found) {"type": "paired", offer_id, temp_key, peer_url, peer_provider, peer_model, tokens_granted, tokens_to_serve}
Client WS disconnect -> matcher.remove_by_ws() cleans up pending offers
```

**Exchange logic**: `tokens_granted = floor(peer_tokens * avg_price(peer_model) / avg_price(your_model))`
where `avg_price = (input_price + output_price) / 2` per 1M tokens.

## COMMANDS

```bash
# Install
pip install -e .

# Run (default 0.0.0.0:8080)
tokenhub-server
# or
python -m server.main

# With custom host/port
HOST=127.0.0.1 PORT=3000 tokenhub-server

# Docker
docker build -t tokenhub-server .
docker run -p 8080:8080 tokenhub-server
```

## NOTES

- No tests or CI exist yet
- Single dependency: `aiohttp>=3.11.0`
- Matching is strictly complementary: A wants B's model AND B wants A's model
- `temp_key` (secrets.token_urlsafe) is generated per pairing for peer auth — not yet consumed by any proxy
- `proxy_url` field supports ngrok tunnels (see commit b1d77d3)
