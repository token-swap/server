import math

# Per 1M tokens: (input_price_usd, output_price_usd)
PRICING: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-5.2": (1.75, 14.00),
    "gpt-5.2-pro": (21.00, 168.00),
    "gpt-5.3-codex": (1.75, 14.00),
    "gpt-5-mini": (0.25, 2.00),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "o3": (2.00, 8.00),
    "o4-mini": (1.10, 4.40),
    # Anthropic
    "claude-opus-4-6": (5.00, 25.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-opus-4-5": (5.00, 25.00),
    # Gemini
    "gemini-3.1-pro-preview": (2.00, 12.00),
    "gemini-3-flash-preview": (0.50, 3.00),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-2.0-flash": (0.10, 0.40),
}

MODEL_ALIASES: dict[str, str] = {
    "gpt-5 mini": "gpt-5-mini",
    "gpt-4.1 mini": "gpt-4.1-mini",
    "gpt-4.1 nano": "gpt-4.1-nano",
    "claude sonnet 4.6": "claude-sonnet-4-6",
    "claude sonnet 4.5": "claude-sonnet-4-5",
    "claude opus 4.6": "claude-opus-4-6",
    "claude opus 4.5": "claude-opus-4-5",
    "claude haiku 4.5": "claude-haiku-4-5",
    "gemini 2.5 pro": "gemini-2.5-pro",
    "gemini 2.5 flash": "gemini-2.5-flash",
    "gemini 2.5 flash lite": "gemini-2.5-flash-lite",
    "gemini 2.0 flash": "gemini-2.0-flash",
}

FAMILY_FALLBACK: dict[str, str] = {
    "gpt-": "gpt-4.1",
    "o": "o4-mini",
    "claude": "claude-sonnet-4-6",
    "gemini": "gemini-2.5-flash",
}

# Precomputed once at module load: PRICING keys sorted by length descending,
# used by _resolve_model() for prefix/substring matching.
_PRICING_KEYS_BY_LENGTH: list[str] = sorted(PRICING.keys(), key=len, reverse=True)


def _normalize_model(model: str) -> str:
    return model.strip().lower().replace("_", "-")


def _resolve_model(model: str) -> str | None:
    normalized = _normalize_model(model)

    if normalized in PRICING:
        return normalized

    if normalized in MODEL_ALIASES:
        alias = MODEL_ALIASES[normalized]
        if alias in PRICING:
            return alias

    for key in _PRICING_KEYS_BY_LENGTH:
        if normalized == key or normalized.startswith(f"{key}-"):
            return key

    for prefix, fallback in FAMILY_FALLBACK.items():
        if normalized.startswith(prefix):
            return fallback

    return None


def avg_price(model: str) -> float:
    resolved = _resolve_model(model)
    if resolved is None:
        raise KeyError(model)
    inp, out = PRICING[resolved]
    return (inp + out) / 2


def input_price(model: str) -> float:
    resolved = _resolve_model(model)
    if resolved is None:
        raise KeyError(model)
    inp, _ = PRICING[resolved]
    return inp


def output_price(model: str) -> float:
    resolved = _resolve_model(model)
    if resolved is None:
        raise KeyError(model)
    _, out = PRICING[resolved]
    return out


def calculate_exchange(
    offered_model: str, offered_tokens: int, wanted_model: str
) -> int:
    return math.floor(
        offered_tokens * avg_price(offered_model) / avg_price(wanted_model)
    )


def calculate_input_exchange(
    offered_model: str, offered_input_tokens: int, wanted_model: str
) -> int:
    return math.floor(
        offered_input_tokens * input_price(offered_model) / input_price(wanted_model)
    )


def calculate_output_exchange(
    offered_model: str, offered_output_tokens: int, wanted_model: str
) -> int:
    return math.floor(
        offered_output_tokens * output_price(offered_model) / output_price(wanted_model)
    )


def is_known_model(model: str) -> bool:
    return _resolve_model(model) is not None
