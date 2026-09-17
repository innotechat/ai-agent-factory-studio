from dataclasses import dataclass
from typing import Any
import httpx
from fastapi import HTTPException

ANTHROPIC_VERSION = "2023-06-01"

@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]

def _is_openrouter_key(api_key: str) -> bool:
    return bool(api_key and api_key.startswith("sk-or-v1-"))

def _safe_error(response: httpx.Response) -> str:
    try:
        data = response.json()
        msg = data.get("error", {}).get("message") or data.get("message")
        if isinstance(msg, str):
            return msg[:500]
    except ValueError:
        pass
    return f"HTTP {response.status_code}"

async def _post_json(url: str, headers: dict, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(url, headers=headers, json=payload)
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"The AI provider responded with an error: {_safe_error(resp)}")
    return resp.json()

async def anthropic_tool_loop(
    base_url: str, api_key: str, model: str, messages: list[dict], specs: list[ToolSpec],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict:
    if _is_openrouter_key(api_key):
        base_url = "https://openrouter.ai/api/v1"
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Voysse",
        }
        tools_payload = [{"type": "function", "function": {"name": s.name, "description": s.description, "parameters": s.parameters}} for s in specs]
        payload: dict = {"model": model, "messages": messages, "tools": tools_payload}
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        data = await _post_json(url, headers, payload)
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        text = msg.get("content") or ""
        tool_calls = []
        for tc in msg.get("tool_calls") or []:
            fn = tc.get("function") or {}
            tool_calls.append({"name": fn.get("name"), "arguments": fn.get("arguments"), "id": tc.get("id")})
        return {"text": text, "tool_calls": tool_calls, "input_tokens": (data.get("usage") or {}).get("prompt_tokens", 0), "output_tokens": (data.get("usage") or {}).get("completion_tokens", 0)}
    else:
        url = f"{base_url.rstrip('/')}/messages"
        headers = {"x-api-key": api_key, "anthropic-version": ANTHROPIC_VERSION, "Content-Type": "application/json"}
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        convo = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] in ("user", "assistant")]
        payload: dict = {"model": model, "messages": convo, "max_tokens": max_tokens or 2048}
        if system:
            payload["system"] = system
        if temperature is not None:
            payload["temperature"] = temperature
        if specs:
            payload["tools"] = [{"name": s.name, "description": s.description, "input_schema": s.parameters} for s in specs]
        data = await _post_json(url, headers, payload)
        parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
        tool_calls = [{"name": b.get("name"), "arguments": b.get("input"), "id": b.get("id")} for b in data.get("content", []) if b.get("type") == "tool_use"]
        usage = data.get("usage") or {}
        return {"text": "".join(parts).strip(), "tool_calls": tool_calls, "input_tokens": usage.get("input_tokens", 0), "output_tokens": usage.get("output_tokens", 0)}

async def openai_tool_loop(
    base_url: str, api_key: str, model: str, messages: list[dict], specs: list[ToolSpec],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict:
    if _is_openrouter_key(api_key):
        base_url = "https://openrouter.ai/api/v1"
    is_openrouter = "openrouter.ai" in base_url
    if is_openrouter:
        url = f"{base_url.rstrip('/')}/chat/completions"
    else:
        url = f"{base_url.rstrip('/')}/responses"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if is_openrouter:
        headers["HTTP-Referer"] = "http://localhost:3000"
        headers["X-Title"] = "Voysse"
    if is_openrouter:
        tools_payload = [{"type": "function", "function": {"name": s.name, "description": s.description, "parameters": s.parameters}} for s in specs]
        payload: dict = {"model": model, "messages": messages}
        if tools_payload:
            payload["tools"] = tools_payload
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        data = await _post_json(url, headers, payload)
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        text = msg.get("content") or ""
        tool_calls = []
        for tc in msg.get("tool_calls") or []:
            fn = tc.get("function") or {}
            tool_calls.append({"name": fn.get("name"), "arguments": fn.get("arguments"), "id": tc.get("id")})
        return {"text": text, "tool_calls": tool_calls, "input_tokens": (data.get("usage") or {}).get("prompt_tokens", 0), "output_tokens": (data.get("usage") or {}).get("completion_tokens", 0)}
    else:
        tools_payload = [{"type": "function", "name": s.name, "description": s.description, "parameters": s.parameters} for s in specs]
        payload: dict = {"model": model, "input": [{"role": m["role"], "content": m["content"]} for m in messages if m["role"]!= "system"]}
        instructions = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        if instructions:
            payload["instructions"] = instructions
        if tools_payload:
            payload["tools"] = tools_payload
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_output_tokens"] = max_tokens
        data = await _post_json(url, headers, payload)
        text = ""
        tool_calls = []
        for item in data.get("output", []):
            if item.get("type") == "message":
                for chunk in item.get("content", []) or []:
                    if chunk.get("type") in ("output_text", "text"):
                        text += chunk.get("text", "")
            if item.get("type") == "function_call":
                tool_calls.append({"name": item.get("name"), "arguments": item.get("arguments"), "id": item.get("call_id")})
        usage = data.get("usage") or {}
        return {"text": text.strip(), "tool_calls": tool_calls, "input_tokens": usage.get("input_tokens", 0), "output_tokens": usage.get("output_tokens", 0)}
