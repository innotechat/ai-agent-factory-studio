"""Data structures and types for the canonical AI Gateway abstraction.

All providers normalize inputs and outputs into these canonical shapes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FinishReason(str, Enum):
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class GatewayMessage:
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: str | None = None
    tool_call_id: str | None = None


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class NormalizedToolCall:
    id: str
    name: str
    arguments: dict[str, Any] | str
    result_preview: str | None = None
    is_error: bool = False


@dataclass(frozen=True)
class GatewayUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    provider: str
    model: str
    request_id: str | None = None


@dataclass
class GatewayResponse:
    text: str
    provider: str
    model: str
    usage: GatewayUsage
    finish_reason: FinishReason = FinishReason.STOP
    tool_calls: list[NormalizedToolCall] = field(default_factory=list)
    raw_response: dict[str, Any] = field(default_factory=dict)
    cached: bool = False


@dataclass(frozen=True)
class ModelCapability:
    supports_tools: bool = True
    supports_vision: bool = False
    supports_streaming: bool = False
    supports_structured_output: bool = False


@dataclass(frozen=True)
class RegisteredModel:
    model_id: str
    provider_id: str
    display_name: str
    family: str
    context_window: int
    max_output_tokens: int
    capabilities: ModelCapability
    input_price_per_1k: float = 0.0
    output_price_per_1k: float = 0.0
    active: bool = True
    badge: str = ""
    note: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResolvedCredential:
    provider_id: str
    api_key: str
    base_url: str
    source: str  # "agency_byok", "platform_managed", "mock"
    agency_id: str | None = None
