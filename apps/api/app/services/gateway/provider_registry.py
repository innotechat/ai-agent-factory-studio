"""Provider Registry for managing and discovering AI provider adapters."""

from typing import Iterable
from .base_adapter import BaseProviderAdapter
from .exceptions import ProviderDisabledError, ProviderNotFoundError
from .adapters.anthropic_adapter import AnthropicAdapter
from .adapters.google_adapter import GoogleGeminiAdapter
from .adapters.mock_adapter import MockProviderAdapter
from .adapters.openai_adapter import OpenAIAdapter


class ProviderRegistry:
    """Central registry of AI provider adapters."""

    def __init__(self, initial_adapters: Iterable[BaseProviderAdapter] | None = None):
        self._adapters: dict[str, BaseProviderAdapter] = {}
        self._enabled: dict[str, bool] = {}

        if initial_adapters:
            for adapter in initial_adapters:
                self.register(adapter)
        else:
            self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(OpenAIAdapter(), enabled=True)
        self.register(AnthropicAdapter(), enabled=True)
        self.register(GoogleGeminiAdapter(), enabled=True)
        self.register(MockProviderAdapter(), enabled=True)

    def register(self, adapter: BaseProviderAdapter, enabled: bool = True) -> None:
        self._adapters[adapter.provider_id] = adapter
        self._enabled[adapter.provider_id] = enabled

    def get_adapter(self, provider_id: str) -> BaseProviderAdapter | None:
        return self._adapters.get(provider_id)

    def require_adapter(self, provider_id: str) -> BaseProviderAdapter:
        adapter = self.get_adapter(provider_id)
        if not adapter:
            raise ProviderNotFoundError(provider_id)
        if not self.is_enabled(provider_id):
            raise ProviderDisabledError(provider_id)
        return adapter

    def is_registered(self, provider_id: str) -> bool:
        return provider_id in self._adapters

    def is_enabled(self, provider_id: str) -> bool:
        return self._enabled.get(provider_id, False)

    def set_enabled(self, provider_id: str, enabled: bool) -> None:
        if provider_id not in self._adapters:
            raise ProviderNotFoundError(provider_id)
        self._enabled[provider_id] = enabled

    def list_providers(self, enabled_only: bool = True) -> list[dict[str, str]]:
        res = []
        for pid, adapter in self._adapters.items():
            if enabled_only and not self.is_enabled(pid):
                continue
            res.append({
                "provider_id": pid,
                "display_name": adapter.display_name,
                "default_base_url": adapter.default_base_url,
                "enabled": self.is_enabled(pid),
            })
        return res


_global_provider_registry = ProviderRegistry()


def get_provider_registry() -> ProviderRegistry:
    return _global_provider_registry
