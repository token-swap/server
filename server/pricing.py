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


def avg_price(model: str) -> float:
    inp, out = PRICING[model]
    return (inp + out) / 2


def calculate_exchange(
    offered_model: str, offered_tokens: int, wanted_model: str
) -> int:
    return math.floor(
        offered_tokens * avg_price(offered_model) / avg_price(wanted_model)
    )


def is_known_model(model: str) -> bool:
    return model in PRICING
