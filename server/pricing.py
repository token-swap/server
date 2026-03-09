import math

# Per 1M tokens: (input_price_usd, output_price_usd). TODO: update pricing for all supported models
PRICING: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-5.4": (2.50, 15.00),
    "gpt-5": (1.25, 10.00),
    "gpt-5.1": (1.25, 10.00),
    "gpt-5.1-codex": (1.25, 10.00),
    "gpt-5.1-codex-max": (1.25, 10.00),
    "gpt-5.1-codex-mini": (0.25, 2.00),
    "gpt-5.2": (1.75, 14.00),
    "gpt-5.2-pro": (21.00, 168.00),
    "gpt-5.2-codex": (1.75, 14.00),
    "gpt-5.3-codex": (1.75, 14.00),
    "gpt-5-mini": (0.25, 2.00),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "gpt-4o": (2.50, 10.00),
    "o3": (2.00, 8.00),
    "o4-mini": (1.10, 4.40),
    # Anthropic
    "claude-opus-4.6": (5.00, 25.00),
    "claude-sonnet-4.6": (3.00, 15.00),
    "claude-haiku-4.5": (1.00, 5.00),
    "claude-sonnet-4": (3.00, 15.00),
    "claude-sonnet-4.5": (3.00, 15.00),
    "claude-opus-4.5": (5.00, 25.00),
    "claude-opus-4-6": (5.00, 25.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-opus-4-5": (5.00, 25.00),
    # Gemini
    "gemini-3-pro-preview": (2.00, 12.00),
    "gemini-3.1-pro-preview": (2.00, 12.00),
    "gemini-3-flash-preview": (0.50, 3.00),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-2.0-flash": (0.10, 0.40),
    "grok-code-fast-1": (0.20, 1.50),
}

SUPPORTED_MODELS_BY_PROVIDER: dict[str, list[str]] = {
    "openai": [
        "gpt-5.2",
        "gpt-5.2-pro",
        "gpt-5.3-codex",
        "gpt-5-mini",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4.1-nano",
        "o3",
        "o4-mini",
    ],
    "anthropic": [
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
        "claude-sonnet-4-5",
        "claude-opus-4-5",
    ],
    "gemini": [
        "gemini-3.1-pro-preview",
        "gemini-3-flash-preview",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
    ],
    "github-copilot": [
        "claude-haiku-4.5",
        "claude-opus-4.5",
        "claude-opus-4.6",
        "claude-sonnet-4",
        "claude-sonnet-4.5",
        "claude-sonnet-4.6",
        "gemini-2.5-pro",
        "gemini-3-flash-preview",
        "gemini-3-pro-preview",
        "gemini-3.1-pro-preview",
        "gpt-4.1",
        "gpt-4o",
        "gpt-5",
        "gpt-5-mini",
        "gpt-5.1",
        "gpt-5.1-codex",
        "gpt-5.1-codex-max",
        "gpt-5.1-codex-mini",
        "gpt-5.2",
        "gpt-5.2-codex",
        "gpt-5.3-codex",
        "gpt-5.4",
        "grok-code-fast-1",
    ],
}


def _resolve_model(model: str) -> str | None:
    # Currently we are matching models with the lists defined above, so new models will not
    # update automatically. This is done to ensure pricing is consistent and for unknown/new
    # models we cannot guarantee that without manual review.
    if model in PRICING:
        return model
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


def get_supported_provider_models(provider: str) -> list[str]:
    return list(SUPPORTED_MODELS_BY_PROVIDER.get(provider, []))
