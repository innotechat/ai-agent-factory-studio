"""Provider Adapter for Google Gemini API."""

import re
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


def redact_secrets(text: str, secret: str | None = None) -> str:
    """Redact secret strings and key= parameters from URLs and exception strings."""
    if not text:
        return text
    # Redact specific secret if supplied
    if secret and len(secret) >= 4:
        text = text.replace(secret, "[REDACTED_API_KEY]")
    # Redact URL query parameters like key=... or api_key=...
    text = re.sub(r'([?&](?:key|api_key|token)=)[^&\s]+', r'\1[REDACTED]', text)
    return text


class GoogleGeminiAdapter(BaseProviderAdapter):
    """Canonical adapter for Google Gemini via Generative Language REST v1beta."""

    def __init__(self, provider_id: str = "google", default_url: str = "https://generativelanguage.googleapis.com/v1beta"):
        self._provider_id = provider_id
        self._default_url = default_url

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def display_name(self) -> str:
        return "Google Gemini"

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
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-pro-preview",
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
        # URL pattern: {base_url}/models/{model}:generateContent?key={api_key}
        clean_model = model.replace("models/", "")
        url = f"{base_url}/models/{clean_model}:generateContent?key={credential.api_key}"
        headers = {"Content-Type": "application/json"}

        contents = []
        system_instruction = None
        system_parts = [m.content for m in messages if m.role == "system"]
        if system_parts:
            system_instruction = {"parts": [{"text": "\n\n".join(system_parts)}]}

        for m in messages:
            if m.role == "system":
                continue
            role = "user" if m.role == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m.content}],
            })

        gen_config: dict[str, Any] = {}
        if temperature is not None:
            gen_config["temperature"] = temperature
        if max_tokens is not None:
            gen_config["maxOutputTokens"] = max_tokens

        payload: dict[str, Any] = {"contents": contents}
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        if gen_config:
            payload["generationConfig"] = gen_config

        if tools:
            func_declarations = [
                {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
                for t in tools
            ]
            payload["tools"] = [{"functionDeclarations": func_declarations}]

        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code >= 400:
                    err_msg = self._extract_error(resp, credential.api_key)
                    raise ProviderExecutionError(self.provider_id, f"HTTP {resp.status_code}: {err_msg}")
                data = resp.json()
        except httpx.HTTPError as exc:
            safe_exc_msg = redact_secrets(str(exc), credential.api_key)
            raise ProviderExecutionError(self.provider_id, f"Connection error: {safe_exc_msg}") from exc

        return self.normalize_response(data, model=model)

    def normalize_response(
        self,
        raw_data: dict[str, Any],
        model: str,
        request_id: str | None = None,
    ) -> GatewayResponse:
        usage_metadata = raw_data.get("usageMetadata") or {}
        in_tokens = int(usage_metadata.get("promptTokenCount") or 0)
        out_tokens = int(usage_metadata.get("candidatesTokenCount") or 0)
        total_tokens = int(usage_metadata.get("totalTokenCount") or (in_tokens + out_tokens))

        usage = GatewayUsage(
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            total_tokens=total_tokens,
            provider=self.provider_id,
            model=model,
            request_id=request_id,
        )

        candidates = raw_data.get("candidates", [])
        if not candidates:
            return GatewayResponse(
                text="",
                provider=self.provider_id,
                model=model,
                usage=usage,
                finish_reason=FinishReason.STOP,
                raw_response=raw_data,
            )

        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        text_parts = []
        tool_calls: list[NormalizedToolCall] = []

        for p in parts:
            if "text" in p:
                text_parts.append(p["text"])
            elif "functionCall" in p:
                fc = p["functionCall"]
                tool_calls.append(
                    NormalizedToolCall(
                        id=fc.get("name", "call_0"),
                        name=fc.get("name", ""),
                        arguments=fc.get("args", {}),
                    )
                )

        raw_finish = candidate.get("finishReason", "STOP")
        finish_reason = self._map_finish_reason(raw_finish)

        return GatewayResponse(
            text="".join(text_parts).strip(),
            provider=self.provider_id,
            model=model,
            usage=usage,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
            raw_response=raw_data,
        )

    def _map_finish_reason(self, reason: str) -> FinishReason:
        r = reason.upper()
        if r in ("STOP",):
            return FinishReason.STOP
        if r in ("MAX_TOKENS",):
            return FinishReason.LENGTH
        if r in ("SAFETY", "RECITATION"):
            return FinishReason.CONTENT_FILTER
        return FinishReason.STOP

    def _extract_error(self, response: httpx.Response, secret: str | None = None) -> str:
        try:
            d = response.json()
            err = d.get("error", {})
            if isinstance(err, dict):
                raw_msg = err.get("message") or str(err)
            else:
                raw_msg = str(d.get("message") or d)
            return redact_secrets(raw_msg, secret)
        except Exception:
            return redact_secrets(response.text[:200], secret)

    async def test_connection(self, credential: ResolvedCredential) -> dict[str, Any]:
        base_url = (credential.base_url or self.default_base_url).rstrip("/")
        url = f"{base_url}/models?key={credential.api_key}"
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(url)
                if resp.status_code >= 400:
                    raise ProviderExecutionError(self.provider_id, self._extract_error(resp, credential.api_key))
                data = resp.json()
                models = [
                    m.get("name", "").replace("models/", "")
                    for m in data.get("models", [])
                    if isinstance(m, dict) and m.get("name")
                ]
                return {"ok": True, "provider": self.provider_id, "models": sorted(models)}
        except httpx.HTTPError as exc:
            safe_msg = redact_secrets(str(exc), credential.api_key)
            raise ProviderExecutionError(self.provider_id, f"Connection error: {safe_msg}") from exc
