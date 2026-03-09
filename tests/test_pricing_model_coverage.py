from server.pricing import PRICING, SUPPORTED_MODELS_BY_PROVIDER


def _all_supported_models() -> set[str]:
    return {
        model
        for provider_models in SUPPORTED_MODELS_BY_PROVIDER.values()
        for model in provider_models
    }


def test_every_priced_model_is_supported_by_at_least_one_provider() -> None:
    priced_models = set(PRICING)
    supported_models = _all_supported_models()

    missing_from_supported = sorted(priced_models - supported_models)

    assert not missing_from_supported, (
        "Models in PRICING missing from SUPPORTED_MODELS_BY_PROVIDER: "
        f"{missing_from_supported}"
    )


def test_every_supported_model_has_pricing_information() -> None:
    priced_models = set(PRICING)
    supported_models = _all_supported_models()

    missing_from_pricing = sorted(supported_models - priced_models)
    providers_by_missing_model = {
        model: sorted(
            provider
            for provider, provider_models in SUPPORTED_MODELS_BY_PROVIDER.items()
            if model in provider_models
        )
        for model in missing_from_pricing
    }

    assert not missing_from_pricing, (
        "Models in SUPPORTED_MODELS_BY_PROVIDER missing from PRICING: "
        f"{missing_from_pricing}; providers={providers_by_missing_model}"
    )
