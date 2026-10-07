"""Canonical Provider Adapter interface.

All model providers must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Any

from .types import (
    FinishReason,
    GatewayMessage,
    GatewayResponse,
    GatewayUsage,
    ModelCapability,
    RegisteredModel,
    ResolvedCredential,
    ToolDefinition,
)


class BaseProviderAdapter(ABC):
    """Abstract base class for all AI provider adapters."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier for this provider (e.g., 'openai', 'anthropic', 'google', 'mock')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider label (e.g. 'OpenAI', 'Anthropic', 'Google Gemini')."""
        pass

    @property
    @abstractmethod
    def default_base_url(self) -> str:
        """Canonical default base URL for this provider."""
        pass

    @abstractmethod
    def capabilities(self) -> ModelCapability:
        """Base capabilities supported by this provider."""
        pass

    @abstractmethod
    def list_models(self) -> list[str]:
        """List model IDs natively supported or verified by this provider."""
        pass

    @abstractmethod
    async def chat(
        self,
        credential: ResolvedCredential,
        model: str,
        messages: list[GatewayMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> GatewayResponse:
        """Execute chat completion and return normalized GatewayResponse."""
        pass

    @abstractmethod
    def normalize_response(
        self,
        raw_data: dict[str, Any],
        model: str,
        request_id: str | None = None,
    ) -> GatewayResponse:
        """Normalize raw provider JSON response into a GatewayResponse."""
        pass

    @abstractmethod
    async def test_connection(self, credential: ResolvedCredential) -> dict[str, Any]:
        """Verify credential connectivity against provider endpoint."""
        pass
