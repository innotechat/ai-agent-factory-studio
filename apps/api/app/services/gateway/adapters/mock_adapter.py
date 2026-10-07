"""Mock Provider Adapter strictly for deterministic testing and resilience verification."""

from typing import Any

from ..base_adapter import BaseProviderAdapter
from ..exceptions import ProviderExecutionError
from ..types import (
    FinishReason,
    GatewayMessage,
    GatewayResponse,
    GatewayUsage,
    ModelCapability,
    NormalizedToolCall,
    ResolvedCredential,
    ToolDefinition,
)


class MockProviderAdapter(BaseProviderAdapter):
    """Deterministic mock provider adapter for tests."""

    def __init__(self, provider_id: str = "mock", default_url: str = "http://mock-provider.local"):
        self._provider_id = provider_id
        self._default_url = default_url
        self.should_fail = False
        self.custom_reply: str | None = None
        self.custom_tool_calls: list[NormalizedToolCall] | None = None
        self.call_history: list[dict[str, Any]] = []

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def display_name(self) -> str:
        return "Mock Provider"

    @property
    def default_base_url(self) -> str:
        return self._default_url

    def capabilities(self) -> ModelCapability:
        return ModelCapability(
            supports_tools=True,
            supports_vision=True,
            supports_streaming=True,
            supports_structured_output=True,
        )

    def list_models(self) -> list[str]:
        return ["mock-fast", "mock-fallback"]

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
        self.call_history.append({
            "credential": credential,
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "tools": tools,
            "kwargs": kwargs,
        })

        if self.should_fail:
            raise ProviderExecutionError(self.provider_id, "Configured test failure in MockProviderAdapter")

        reply_text = self.custom_reply or f"Mock reply to: {messages[-1].content if messages else ''}"
        tool_calls = self.custom_tool_calls or []
        finish_reason = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP

        usage = GatewayUsage(
            input_tokens=15,
            output_tokens=25,
            total_tokens=40,
            provider=self.provider_id,
            model=model,
            request_id="mock-req-12345",
        )

        return GatewayResponse(
            text=reply_text,
            provider=self.provider_id,
            model=model,
            usage=usage,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
            raw_response={"mock": True, "reply": reply_text},
        )

    def normalize_response(
        self,
        raw_data: dict[str, Any],
        model: str,
        request_id: str | None = None,
    ) -> GatewayResponse:
        return GatewayResponse(
            text=raw_data.get("reply", "Normalized mock text"),
            provider=self.provider_id,
            model=model,
            usage=GatewayUsage(10, 20, 30, self.provider_id, model, request_id),
            raw_response=raw_data,
        )

    async def test_connection(self, credential: ResolvedCredential) -> dict[str, Any]:
        if self.should_fail:
            raise ProviderExecutionError(self.provider_id, "Mock connection test failed")
        return {"ok": True, "provider": self.provider_id, "models": self.list_models()}
