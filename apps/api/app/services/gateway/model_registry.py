"""Centralized Model Registry for the AI Gateway."""

from typing import Iterable
from .exceptions import ModelNotFoundError
from .types import ModelCapability, RegisteredModel

# Canonical model catalog definitions based on backend source of truth
DEFAULT_MODELS: list[RegisteredModel] = [
    # OpenAI
    RegisteredModel(
        model_id="gpt-5.6-luna",
        provider_id="openai",
        display_name="GPT-5.6 Luna",
        family="gpt-5.6",
        context_window=400_000,
        max_output_tokens=16_384,
        capabilities=ModelCapability(supports_tools=True, supports_vision=True, supports_streaming=True, supports_structured_output=True),
        input_price_per_1k=0.0004,
        output_price_per_1k=0.0016,
        badge="Most affordable",
        note="High volume, chat and cost-sensitive automations.",
    ),
    RegisteredModel(
        model_id="gpt-5.6-terra",
        provider_id="openai",
        display_name="GPT-5.6 Terra",
        family="gpt-5.6",
        context_window=400_000,
        max_output_tokens=32_768,
        capabilities=ModelCapability(supports_tools=True, supports_vision=True, supports_streaming=True, supports_structured_output=True),
        input_price_per_1k=0.0015,
        output_price_per_1k=0.006,
        badge="Balanced",
        note="A good balance of capability, speed and price.",
    ),
    RegisteredModel(
        model_id="gpt-5.6-sol",
        provider_id="openai",
        display_name="GPT-5.6 Sol",
        family="gpt-5.6",
        context_window=400_000,
        max_output_tokens=65_536,
        capabilities=ModelCapability(supports_tools=True, supports_vision=True, supports_streaming=True, supports_structured_output=True),
        input_price_per_1k=0.005,
        output_price_per_1k=0.02,
        badge="Top capability",
        note="Complex work and more demanding responses.",
    ),
    RegisteredModel(
        model_id="gpt-5.6",
        provider_id="openai",
        display_name="GPT-5.6",
        family="gpt-5.6",
        context_window=400_000,
        max_output_tokens=65_536,
        capabilities=ModelCapability(supports_tools=True, supports_vision=True, supports_streaming=True, supports_structured_output=True),
        input_price_per_1k=0.005,
        output_price_per_1k=0.02,
        badge="Alias of Sol",
        note="Official alias pointing to the GPT-5.6 Sol model.",
    ),
    RegisteredModel(
        model_id="gpt-5.5",
        provider_id="openai",
        display_name="GPT-5.5",
        family="gpt-5.5",
        context_window=256_000,
        max_output_tokens=32_768,
        capabilities=ModelCapability(supports_tools=True, supports_vision=True, supports_streaming=True, supports_structured_output=True),
        input_price_per_1k=0.004,
        output_price_per_1k=0.016,
        badge="Previous generation",
        note="Available for compatibility and gradual migrations.",
    ),
    # Google Gemini
    RegisteredModel(
        model_id="gemini-3.6-flash",
        provider_id="google",
        display_name="Gemini 3.6 Flash",
        family="gemini-3",
        context_window=1_000_000,
        max_output_tokens=65_536,
        capabilities=ModelCapability(supports_tools=True, supports_vision=True, supports_streaming=True, supports_structured_output=True),
        input_price_per_1k=0.0003,
        output_price_per_1k=0.0025,
        badge="Current",
        note="Fast, balanced model for agents and applications.",
    ),
    RegisteredModel(
        model_id="gemini-3.5-flash",
        provider_id="google",
        display_name="Gemini 3.5 Flash",
        family="gemini-3",
        context_window=1_000_000,
        max_output_tokens=65_536,
        capabilities=ModelCapability(supports_tools=True, supports_vision=True, supports_streaming=True, supports_structured_output=True),
        input_price_per_1k=0.0003,
        output_price_per_1k=0.0025,
        badge="Stable",
        note="General low-latency option with a wide context.",
    ),
    RegisteredModel(
        model_id="gemini-3.5-flash-lite",
        provider_id="google",
        display_name="Gemini 3.5 Flash-Lite",
        family="gemini-3",
        context_window=1_000_000,
        max_output_tokens=65_536,
        capabilities=ModelCapability(supports_tools=True, supports_vision=False, supports_streaming=True, supports_structured_output=True),
        input_price_per_1k=0.0001,
        output_price_per_1k=0.0004,
        badge="Economical",
        note="The lowest-cost alternative in the Gemini 3.5 family.",
    ),
    RegisteredModel(
        model_id="gemini-3.1-pro-preview",
        provider_id="google",
        display_name="Gemini 3.1 Pro Preview",
        family="gemini-3",
        context_window=1_000_000,
        max_output_tokens=65_536,
        capabilities=ModelCapability(supports_tools=True, supports_vision=True, supports_streaming=True, supports_structured_output=True),
        input_price_per_1k=0.00125,
        output_price_per_1k=0.01,
        badge="Preview",
        note="Advanced reasoning; try it first in controlled tests.",
    ),
    # Anthropic
    RegisteredModel(
        model_id="claude-opus-4-7",
        provider_id="anthropic",
        display_name="Claude Opus 4.7",
        family="claude",
        context_window=200_000,
        max_output_tokens=32_768,
        capabilities=ModelCapability(supports_tools=True, supports_vision=True, supports_streaming=True, supports_structured_output=True),
        input_price_per_1k=0.005,
        output_price_per_1k=0.025,
        badge="Top capability",
        note="Complex tasks, reasoning and demanding agent flows.",
    ),
    RegisteredModel(
        model_id="claude-sonnet-4-6",
        provider_id="anthropic",
        display_name="Claude Sonnet 4.6",
        family="claude",
        context_window=200_000,
        max_output_tokens=16_384,
        capabilities=ModelCapability(supports_tools=True, supports_vision=True, supports_streaming=True, supports_structured_output=True),
        input_price_per_1k=0.003,
        output_price_per_1k=0.015,
        badge="Balanced",
        note="A mix of speed and intelligence for production.",
    ),
    RegisteredModel(
        model_id="claude-haiku-4-5",
        provider_id="anthropic",
        display_name="Claude Haiku 4.5",
        family="claude",
        context_window=200_000,
        max_output_tokens=8_192,
        capabilities=ModelCapability(supports_tools=True, supports_vision=True, supports_streaming=True, supports_structured_output=True),
        input_price_per_1k=0.0008,
        output_price_per_1k=0.004,
        badge="Fast",
        note="Quick responses and simpler workloads.",
    ),
    # Mock Provider Models (for tests and verification)
    RegisteredModel(
        model_id="mock-fast",
        provider_id="mock",
        display_name="Mock Fast Model",
        family="mock",
        context_window=100_000,
        max_output_tokens=4_096,
        capabilities=ModelCapability(supports_tools=True, supports_vision=True, supports_streaming=True, supports_structured_output=True),
        input_price_per_1k=0.0001,
        output_price_per_1k=0.0002,
        badge="Test",
        note="Deterministic unit and integration testing model.",
    ),
    RegisteredModel(
        model_id="mock-fallback",
        provider_id="mock",
        display_name="Mock Fallback Model",
        family="mock",
        context_window=100_000,
        max_output_tokens=4_096,
        capabilities=ModelCapability(supports_tools=True, supports_vision=False, supports_streaming=True, supports_structured_output=True),
        input_price_per_1k=0.0001,
        output_price_per_1k=0.0002,
        badge="Test Fallback",
        note="Deterministic fallback testing model.",
    ),
]


class ModelRegistry:
    """In-memory source of truth for AI models."""

    def __init__(self, initial_models: Iterable[RegisteredModel] | None = None):
        self._models: dict[str, RegisteredModel] = {}
        for model in initial_models or DEFAULT_MODELS:
            self.register_model(model)

    def register_model(self, model: RegisteredModel) -> None:
        self._models[model.model_id] = model

    def get_model(self, model_id: str) -> RegisteredModel | None:
        return self._models.get(model_id)

    def require_model(self, model_id: str) -> RegisteredModel:
        model = self.get_model(model_id)
        if not model:
            raise ModelNotFoundError(model_id)
        return model

    def list_models(self, provider_id: str | None = None, active_only: bool = True) -> list[RegisteredModel]:
        models = list(self._models.values())
        if provider_id:
            models = [m for m in models if m.provider_id == provider_id]
        if active_only:
            models = [m for m in models if m.active]
        return models

    def is_registered(self, model_id: str) -> bool:
        return model_id in self._models


_global_model_registry = ModelRegistry()


def get_model_registry() -> ModelRegistry:
    return _global_model_registry
