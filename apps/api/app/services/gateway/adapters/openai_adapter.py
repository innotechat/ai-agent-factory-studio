"""Provider Adapter for OpenAI compatible endpoints."""

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


class OpenAIAdapter(BaseProviderAdapter):
    """Canonical adapter for OpenAI (and compatible endpoints like OpenRouter)."""

    def __init__(self, provider_id: str = "openai", default_url: str = "https://api.openai.com/v1"):
        self._provider_id = provider_id
        self._default_url = default_url

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def display_name(self) -> str:
        return "OpenAI"

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
            "gpt-5.6-luna",
            "gpt-5.6-terra",
            "gpt-5.6-sol",
            "gpt-5.6",
            "gpt-5.5",
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
        is_openrouter = "openrouter.ai" in base_url

        url = f"{base_url}/chat/completions" if is_openrouter else f"{base_url}/responses"
        headers = {
            "Authorization": f"Bearer {credential.api_key}",
            "Content-Type": "application/json",
        }
        if is_openrouter:
            headers["HTTP-Referer"] = "http://localhost:3000"
            headers["X-Title"] = "InnoTech Gateway"

        if is_openrouter:
            openai_messages = []
            for m in messages:
                msg_dict = {"role": m.role, "content": m.content}
                if m.name:
                    msg_dict["name"] = m.name
                if m.tool_call_id:
                    msg_dict["tool_call_id"] = m.tool_call_id
                openai_messages.append(msg_dict)

            payload: dict[str, Any] = {"model": model, "messages": openai_messages}
            if temperature is not None:
                payload["temperature"] = temperature
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            if tools:
                payload["tools"] = [
                    {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.parameters,
                        },
                    }
                    for t in tools
                ]
        else:
            # Native OpenAI Responses API payload
            instructions = "\n\n".join(m.content for m in messages if m.role == "system")
            input_items = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
            payload = {"model": model, "input": input_items}
            if instructions:
                payload["instructions"] = instructions
            if temperature is not None:
                payload["temperature"] = temperature
            if max_tokens is not None:
                payload["max_output_tokens"] = max_tokens
            if tools:
                payload["tools"] = [
                    {
                        "type": "function",
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
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
        in_tokens = int(usage_data.get("prompt_tokens") or usage_data.get("input_tokens") or 0)
        out_tokens = int(usage_data.get("completion_tokens") or usage_data.get("output_tokens") or 0)
        total_tokens = in_tokens + out_tokens

        usage = GatewayUsage(
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            total_tokens=total_tokens,
            provider=self.provider_id,
            model=model,
            request_id=req_id,
        )

        choices = raw_data.get("choices")
        if choices:
            # Chat completions format
            choice = choices[0]
            msg = choice.get("message") or {}
            text = (msg.get("content") or "").strip()
            raw_finish = choice.get("finish_reason") or "stop"
            tool_calls: list[NormalizedToolCall] = []
            for tc in msg.get("tool_calls") or []:
                fn = tc.get("function") or {}
                tool_calls.append(
                    NormalizedToolCall(
                        id=tc.get("id", ""),
                        name=fn.get("name", ""),
                        arguments=fn.get("arguments", {}),
                    )
                )
            finish_reason = self._map_finish_reason(raw_finish)
            return GatewayResponse(
                text=text,
                provider=self.provider_id,
                model=model,
                usage=usage,
                finish_reason=finish_reason,
                tool_calls=tool_calls,
                raw_response=raw_data,
            )

        # Responses API format
        convenience = raw_data.get("output_text")
        text = ""
        tool_calls = []
        if isinstance(convenience, str) and convenience.strip():
            text = convenience.strip()
        else:
            parts = []
            for item in raw_data.get("output", []):
                if item.get("type") == "message":
                    for chunk in item.get("content", []) or []:
                        if chunk.get("type") in ("output_text", "text"):
                            parts.append(chunk.get("text", ""))
                elif item.get("type") == "function_call":
                    tool_calls.append(
                        NormalizedToolCall(
                            id=item.get("call_id", ""),
                            name=item.get("name", ""),
                            arguments=item.get("arguments", {}),
                        )
                    )
            text = "".join(parts).strip()

        finish_reason = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
        return GatewayResponse(
            text=text,
            provider=self.provider_id,
            model=model,
            usage=usage,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
            raw_response=raw_data,
        )

    def _map_finish_reason(self, reason: str) -> FinishReason:
        r = reason.lower()
        if r in ("stop", "end_turn"):
            return FinishReason.STOP
        if r in ("length", "max_tokens"):
            return FinishReason.LENGTH
        if r in ("tool_calls", "function_call"):
            return FinishReason.TOOL_CALLS
        if r in ("content_filter", "safety"):
            return FinishReason.CONTENT_FILTER
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
        headers = {"Authorization": f"Bearer {credential.api_key}"}
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
