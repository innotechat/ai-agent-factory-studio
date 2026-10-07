"""Unit and integration tests for AI Gateway and Provider / Model abstraction."""

import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.services.gateway import (
    AIGateway,
    CredentialResolutionError,
    CredentialResolver,
    FinishReason,
    GatewayError,
    GatewayMessage,
    GatewayResponse,
    GatewayUsage,
    ModelCapability,
    ModelCapabilityMismatchError,
    ModelNotFoundError,
    ModelRegistry,
    NormalizedToolCall,
    ProviderDisabledError,
    ProviderNotFoundError,
    ProviderRegistry,
    RegisteredModel,
    ResolvedCredential,
    RouteDecision,
    RoutingPolicy,
    TenantSecurityError,
    ToolDefinition,
    get_model_registry,
    get_provider_registry,
)
from app.services.gateway.adapters.anthropic_adapter import AnthropicAdapter
from app.services.gateway.adapters.google_adapter import GoogleGeminiAdapter
from app.services.gateway.adapters.mock_adapter import MockProviderAdapter
from app.services.gateway.adapters.openai_adapter import OpenAIAdapter


# ==========================================
# 1. Provider Registry Tests
# ==========================================

def test_provider_registry_default_registration_and_lookup():
    reg = ProviderRegistry()
    assert reg.is_registered("openai")
    assert reg.is_registered("anthropic")
    assert reg.is_registered("google")
    assert reg.is_registered("mock")

    openai_adapter = reg.require_adapter("openai")
    assert isinstance(openai_adapter, OpenAIAdapter)
    assert openai_adapter.display_name == "OpenAI"

    anthropic_adapter = reg.require_adapter("anthropic")
    assert isinstance(anthropic_adapter, AnthropicAdapter)

    google_adapter = reg.require_adapter("google")
    assert isinstance(google_adapter, GoogleGeminiAdapter)


def test_provider_registry_unknown_provider():
    reg = ProviderRegistry()
    with pytest.raises(ProviderNotFoundError):
        reg.require_adapter("unknown-provider-xyz")


def test_provider_registry_disabled_state():
    reg = ProviderRegistry()
    assert reg.is_enabled("openai")
    reg.set_enabled("openai", False)
    assert not reg.is_enabled("openai")

    with pytest.raises(ProviderDisabledError):
        reg.require_adapter("openai")

    reg.set_enabled("openai", True)
    assert reg.is_enabled("openai")
    assert reg.require_adapter("openai") is not None


# ==========================================
# 2. Model Registry Tests
# ==========================================

def test_model_registry_lookup_and_metadata():
    reg = ModelRegistry()
    model = reg.require_model("gpt-5.6-luna")
    assert model.provider_id == "openai"
    assert model.context_window == 400_000
    assert model.capabilities.supports_tools is True
    assert model.capabilities.supports_vision is True

    gemini = reg.require_model("gemini-3.6-flash")
    assert gemini.provider_id == "google"
    assert gemini.context_window == 1_000_000

    claude = reg.require_model("claude-opus-4-7")
    assert claude.provider_id == "anthropic"


def test_model_registry_unknown_model():
    reg = ModelRegistry()
    assert reg.get_model("invented-model-123") is None
    with pytest.raises(ModelNotFoundError):
        reg.require_model("invented-model-123")


def test_model_registry_filtering():
    reg = ModelRegistry()
    openai_models = reg.list_models(provider_id="openai")
    assert len(openai_models) >= 5
    assert all(m.provider_id == "openai" for m in openai_models)


# ==========================================
# 3. Routing Policy Tests
# ==========================================

def test_routing_policy_deterministic_selection():
    routing = RoutingPolicy()
    decision = routing.resolve_route("gpt-5.6-luna")
    assert decision.primary_provider == "openai"
    assert decision.primary_model == "gpt-5.6-luna"
    assert decision.requires_tools is False

    gemini_decision = routing.resolve_route("gemini-3.6-flash")
    assert gemini_decision.primary_provider == "google"
    assert gemini_decision.primary_model == "gemini-3.6-flash"


def test_routing_policy_capability_validation():
    reg = ModelRegistry()
    # Register a model without tools support
    no_tool_model = RegisteredModel(
        model_id="no-tools-model",
        provider_id="mock",
        display_name="No Tools Model",
        family="test",
        context_window=1000,
        max_output_tokens=1000,
        capabilities=ModelCapability(supports_tools=False, supports_vision=False),
    )
    reg.register_model(no_tool_model)
    routing = RoutingPolicy(model_registry=reg)

    with pytest.raises(ModelCapabilityMismatchError):
        routing.resolve_route("no-tools-model", requires_tools=True)

    with pytest.raises(ModelCapabilityMismatchError):
        routing.resolve_route("no-tools-model", requires_vision=True)


def test_routing_policy_deterministic_fallback():
    routing = RoutingPolicy()
    decision = routing.resolve_route("mock-fast")
    assert decision.primary_model == "mock-fast"
    assert decision.fallback_provider == "mock"
    assert decision.fallback_model == "mock-fallback"

    openai_decision = routing.resolve_route("gpt-5.6-sol")
    assert openai_decision.fallback_model == "gpt-5.6-terra"


# ==========================================
# 4. Credential Resolver Tests (Mock DB / Isolation)
# ==========================================

class FakeQuery:
    def __init__(self, result=None):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._result


class FakeDBSession:
    def __init__(self, cred_row=None):
        self.cred_row = cred_row

    def scalar(self, statement):
        return self.cred_row


def test_credential_resolver_mock_provider():
    db = FakeDBSession()
    resolver = CredentialResolver(db)
    agency_id = uuid.uuid4()
    resolved = resolver.resolve("mock", agency_id)
    assert resolved.provider_id == "mock"
    assert resolved.source == "mock"
    assert resolved.base_url == "http://mock-provider.local"
    # Never expose frontend or insecure credentials


def test_credential_resolver_tenant_isolation_mismatch():
    db = FakeDBSession()
    resolver = CredentialResolver(db)
    agency_1 = uuid.uuid4()
    agency_2 = uuid.uuid4()
    user = SimpleNamespace(agency_id=agency_1)

    with pytest.raises(TenantSecurityError):
        resolver.resolve("mock", agency_2, user=user)


def test_credential_resolver_missing_credential_raises():
    db = FakeDBSession(cred_row=None)
    resolver = CredentialResolver(db)
    agency_id = uuid.uuid4()

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(CredentialResolutionError):
            resolver.resolve("openai", agency_id)


# ==========================================
# 5. Gateway End-to-End Execution Flow Tests
# ==========================================

@pytest.mark.asyncio
async def test_gateway_flow_principal_tenant_routing_adapter():
    db = FakeDBSession()
    mock_adapter = MockProviderAdapter()
    provider_reg = ProviderRegistry([mock_adapter])
    model_reg = ModelRegistry()

    gateway = AIGateway(
        db=db,
        provider_registry=provider_reg,
        model_registry=model_reg,
    )

    agency_id = uuid.uuid4()
    user = SimpleNamespace(agency_id=agency_id)
    messages = [GatewayMessage(role="user", content="Hello InnoTech")]

    response = await gateway.complete(
        agency_id=agency_id,
        user=user,
        model="mock-fast",
        messages=messages,
    )

    assert isinstance(response, GatewayResponse)
    assert response.provider == "mock"
    assert response.model == "mock-fast"
    assert response.finish_reason == FinishReason.STOP
    assert "Mock reply to: Hello InnoTech" in response.text
    assert response.usage.input_tokens == 15
    assert response.usage.output_tokens == 25
    assert response.usage.total_tokens == 40


@pytest.mark.asyncio
async def test_gateway_fallback_on_primary_failure():
    db = FakeDBSession()
    mock_adapter = MockProviderAdapter()
    mock_adapter.should_fail = True  # force primary to fail

    provider_reg = ProviderRegistry([mock_adapter])
    model_reg = ModelRegistry()

    gateway = AIGateway(
        db=db,
        provider_registry=provider_reg,
        model_registry=model_reg,
    )

    agency_id = uuid.uuid4()
    user = SimpleNamespace(agency_id=agency_id)
    messages = [GatewayMessage(role="user", content="Hello InnoTech")]

    # If mock_adapter fails for all calls, it raises ProviderExecutionError
    with pytest.raises(GatewayError):
        await gateway.complete(
            agency_id=agency_id,
            user=user,
            model="mock-fast",
            messages=messages,
            allow_fallback=True,
        )


# ==========================================
# 6. Usage Normalization Fixtures Tests
# ==========================================

def test_openai_response_normalization():
    adapter = OpenAIAdapter()
    raw_fixture = {
        "id": "chatcmpl-test-123",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Normalized OpenAI completion",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 102,
            "completion_tokens": 48,
            "total_tokens": 150,
        },
    }

    normalized = adapter.normalize_response(raw_fixture, model="gpt-5.6-luna")
    assert normalized.text == "Normalized OpenAI completion"
    assert normalized.provider == "openai"
    assert normalized.model == "gpt-5.6-luna"
    assert normalized.usage.input_tokens == 102
    assert normalized.usage.output_tokens == 48
    assert normalized.usage.total_tokens == 150
    assert normalized.finish_reason == FinishReason.STOP


def test_anthropic_response_normalization():
    adapter = AnthropicAdapter()
    raw_fixture = {
        "id": "msg_test_456",
        "type": "message",
        "role": "assistant",
        "content": [
            {"type": "text", "text": "Normalized Anthropic completion"}
        ],
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 80,
            "output_tokens": 40,
        },
    }

    normalized = adapter.normalize_response(raw_fixture, model="claude-sonnet-4-6")
    assert normalized.text == "Normalized Anthropic completion"
    assert normalized.provider == "anthropic"
    assert normalized.model == "claude-sonnet-4-6"
    assert normalized.usage.input_tokens == 80
    assert normalized.usage.output_tokens == 40
    assert normalized.usage.total_tokens == 120
    assert normalized.finish_reason == FinishReason.STOP


def test_google_gemini_response_normalization():
    adapter = GoogleGeminiAdapter()
    raw_fixture = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Normalized Google Gemini completion"}],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 210,
            "candidatesTokenCount": 65,
            "totalTokenCount": 275,
        },
    }

    normalized = adapter.normalize_response(raw_fixture, model="gemini-3.6-flash")
    assert normalized.text == "Normalized Google Gemini completion"
    assert normalized.provider == "google"
    assert normalized.model == "gemini-3.6-flash"
    assert normalized.usage.input_tokens == 210
    assert normalized.usage.output_tokens == 65
    assert normalized.usage.total_tokens == 275
    assert normalized.finish_reason == FinishReason.STOP
