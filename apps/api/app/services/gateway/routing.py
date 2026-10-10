"""Deterministic Routing Policy for the AI Gateway.

Determines:
- primary provider and model
- fallback provider and model
- capability validation (e.g. tools, vision)
"""

from dataclasses import dataclass
from typing import Any

from .exceptions import (
    ModelCapabilityMismatchError,
    ModelInactiveError,
    ProviderModelMismatchError,
    RoutingError,
)
from .model_registry import ModelRegistry, get_model_registry
from .provider_registry import ProviderRegistry, get_provider_registry
from .types import RegisteredModel


@dataclass(frozen=True)
class RouteDecision:
    primary_provider: str
    primary_model: str
    fallback_provider: str | None = None
    fallback_model: str | None = None
    requires_tools: bool = False
    requires_vision: bool = False


class RoutingPolicy:
    """Server-side deterministic routing engine."""

    def __init__(
        self,
        model_registry: ModelRegistry | None = None,
        provider_registry: ProviderRegistry | None = None,
    ):
        self.model_registry = model_registry or get_model_registry()
        self.provider_registry = provider_registry or get_provider_registry()

    def resolve_route(
        self,
        requested_model: str,
        requested_provider: str | None = None,
        *,
        requires_tools: bool = False,
        requires_vision: bool = False,
        allow_fallback: bool = True,
        custom_fallback_model: str | None = None,
    ) -> RouteDecision:
        """Deterministically choose provider, model, and eligible fallback."""
        model_info = self.model_registry.get_model(requested_model)
        if not model_info:
            raise RoutingError(f"Requested model '{requested_model}' not found in registry.")

        # Ensure model is active and verified
        if not model_info.active:
            raise ModelInactiveError(model_info.model_id)

        # Strict Provider <-> Model Binding validation
        if requested_provider:
            req_prov = requested_provider.strip().lower()
            actual_prov = model_info.provider_id.strip().lower()
            if req_prov != actual_prov:
                raise ProviderModelMismatchError(
                    requested_provider=requested_provider,
                    model_id=model_info.model_id,
                    actual_provider=model_info.provider_id,
                )
            provider = model_info.provider_id
        else:
            provider = model_info.provider_id

        # Capability validation
        if requires_tools and not model_info.capabilities.supports_tools:
            raise ModelCapabilityMismatchError(requested_model, "tools")
        if requires_vision and not model_info.capabilities.supports_vision:
            raise ModelCapabilityMismatchError(requested_model, "vision")

        # Determine fallback if permitted
        fallback_provider = None
        fallback_model = None

        if allow_fallback:
            if custom_fallback_model:
                fb_info = self.model_registry.get_model(custom_fallback_model)
                if not fb_info:
                    raise RoutingError(f"Custom fallback model '{custom_fallback_model}' not found in registry.")
                if not fb_info.active:
                    raise ModelInactiveError(fb_info.model_id)
                # Verify provider is registered and enabled
                if not self.provider_registry.is_registered(fb_info.provider_id) or not self.provider_registry.is_enabled(fb_info.provider_id):
                    raise RoutingError(f"Provider '{fb_info.provider_id}' for fallback model '{custom_fallback_model}' is not active or registered.")
                # Verify required capabilities
                if requires_tools and not fb_info.capabilities.supports_tools:
                    raise ModelCapabilityMismatchError(custom_fallback_model, "tools")
                if requires_vision and not fb_info.capabilities.supports_vision:
                    raise ModelCapabilityMismatchError(custom_fallback_model, "vision")
                fallback_provider = fb_info.provider_id
                fallback_model = fb_info.model_id
            else:
                # Deterministic family fallback
                fallback_model_info = self._find_deterministic_fallback(model_info, requires_tools, requires_vision)
                if fallback_model_info and fallback_model_info.active:
                    if self.provider_registry.is_registered(fallback_model_info.provider_id) and self.provider_registry.is_enabled(fallback_model_info.provider_id):
                        fallback_provider = fallback_model_info.provider_id
                        fallback_model = fallback_model_info.model_id

        return RouteDecision(
            primary_provider=provider,
            primary_model=model_info.model_id,
            fallback_provider=fallback_provider,
            fallback_model=fallback_model,
            requires_tools=requires_tools,
            requires_vision=requires_vision,
        )

    def _find_deterministic_fallback(
        self,
        primary: RegisteredModel,
        requires_tools: bool,
        requires_vision: bool,
    ) -> RegisteredModel | None:
        """Find deterministic fallback model with compatible capabilities."""
        # For mock provider, fallback to mock-fallback
        if primary.provider_id == "mock":
            if primary.model_id == "mock-fast":
                return self.model_registry.get_model("mock-fallback")
            return None

        # For OpenAI models, fallback to balanced gpt-5.6-terra or luna
        if primary.provider_id == "openai":
            if primary.model_id in ("gpt-5.6-sol", "gpt-5.6"):
                return self.model_registry.get_model("gpt-5.6-terra")
            if primary.model_id == "gpt-5.6-terra":
                return self.model_registry.get_model("gpt-5.6-luna")

        # For Anthropic, fallback from Opus to Sonnet
        if primary.provider_id == "anthropic":
            if primary.model_id == "claude-opus-4-7":
                return self.model_registry.get_model("claude-sonnet-4-6")
            if primary.model_id == "claude-sonnet-4-6":
                return self.model_registry.get_model("claude-haiku-4-5")

        # For Google Gemini, fallback to flash
        if primary.provider_id == "google":
            if primary.model_id == "gemini-3.1-pro-preview":
                return self.model_registry.get_model("gemini-3.6-flash")
            if primary.model_id == "gemini-3.6-flash":
                return self.model_registry.get_model("gemini-3.5-flash")

        return None
