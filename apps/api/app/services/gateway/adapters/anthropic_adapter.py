"""Provider Adapter for Anthropic Claude Messages API."""

from typing import Any
import httpx

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

ANTHROPIC_VERSION = "2023-06-01"


class AnthropicAdapter(BaseProviderAdapter):
    """Canonical adapter for Anthropic Claude."""

    def __init__(self, provider_id: str = "anthropic", default_url: str = "https://api.anthropic.com/v1"):
        self._provider_id = provider_id
        self._default_url = default_url

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def display_name(self) -> str:
        return "Anthropic"

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
        return [
            "claude-opus-4-7",
            "claude-sonnet-4-6",
            "claude-haiku-4-5",
        ]

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
        base_url = (credential.base_url or self.default_base_url).rstrip("/")
        url = f"{base_url}/messages"
        headers = {
            "x-api-key": credential.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }

        system_parts = [m.content for m in messages if m.role == "system"]
        system = "\n\n".join(system_parts) if system_parts else None

        convo = []
        for m in messages:
            if m.role in ("user", "assistant"):
                convo.append({"role": m.role, "content": m.content})
            elif m.role == "tool":
                convo.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": m.tool_call_id or "",
                            "content": m.content,
                        }
                    ],
                })

        payload: dict[str, Any] = {
            "model": model,
            "messages": convo,
            "max_tokens": max_tokens or 2048,
        }
        if system:
            payload["system"] = system
        if temperature is not None:
            payload["temperature"] = temperature
        if tools:
            payload["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.parameters,
                }
                for t in tools
            ]

        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code >= 400:
                    err_msg = self._extract_error(resp)
                    raise ProviderExecutionError(self.provider_id, f"HTTP {resp.status_code}: {err_msg}")
                data = resp.json()
        except httpx.HTTPError as exc:
            raise ProviderExecutionError(self.provider_id, f"Connection error: {str(exc)}") from exc

        return self.normalize_response(data, model=model)

    def normalize_response(
        self,
        raw_data: dict[str, Any],
        model: str,
        request_id: str | None = None,
    ) -> GatewayResponse:
        req_id = request_id or raw_data.get("id")
        usage_data = raw_data.get("usage") or {}
        in_tokens = int(usage_data.get("input_tokens") or 0)
        out_tokens = int(usage_data.get("output_tokens") or 0)
        total_tokens = in_tokens + out_tokens

        usage = GatewayUsage(
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            total_tokens=total_tokens,
            provider=self.provider_id,
            model=model,
            request_id=req_id,
        )

        content_blocks = raw_data.get("content", [])
        text_parts = []
        tool_calls: list[NormalizedToolCall] = []

        for block in content_blocks:
            b_type = block.get("type")
            if b_type == "text":
                text_parts.append(block.get("text", ""))
            elif b_type == "tool_use":
                tool_calls.append(
                    NormalizedToolCall(
                        id=block.get("id", ""),
                        name=block.get("name", ""),
                        arguments=block.get("input", {}),
                    )
                )

        text = "".join(text_parts).strip()
        stop_reason = raw_data.get("stop_reason") or "end_turn"
        finish_reason = self._map_stop_reason(stop_reason)

        return GatewayResponse(
            text=text,
            provider=self.provider_id,
            model=model,
            usage=usage,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
            raw_response=raw_data,
        )

    def _map_stop_reason(self, reason: str) -> FinishReason:
        r = reason.lower()
        if r in ("end_turn", "stop_sequence"):
            return FinishReason.STOP
        if r in ("max_tokens",):
            return FinishReason.LENGTH
        if r in ("tool_use",):
            return FinishReason.TOOL_CALLS
        return FinishReason.UNKNOWN

    def _extract_error(self, response: httpx.Response) -> str:
        try:
            d = response.json()
            err = d.get("error", {})
            if isinstance(err, dict):
                return err.get("message") or str(err)
            return str(d.get("message") or d)
        except Exception:
            return response.text[:200]

    async def test_connection(self, credential: ResolvedCredential) -> dict[str, Any]:
        base_url = (credential.base_url or self.default_base_url).rstrip("/")
        headers = {
            "x-api-key": credential.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        }
        url = f"{base_url}/models"
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code >= 400:
                    raise ProviderExecutionError(self.provider_id, self._extract_error(resp))
                data = resp.json()
                models = [
                    item.get("id")
                    for item in data.get("data", [])
                    if isinstance(item, dict) and item.get("id")
                ]
                return {"ok": True, "provider": self.provider_id, "models": sorted(models)}
        except httpx.HTTPError as exc:
            raise ProviderExecutionError(self.provider_id, f"Connection error: {str(exc)}") from exc
