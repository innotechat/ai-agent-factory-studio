"""Unit and integration tests for AI Gateway and Provider / Model abstraction."""

import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.config import Settings
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
    ProviderExecutionError,
    ProviderModelMismatchError,
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
from app.services.gateway.adapters.google_adapter import GoogleGeminiAdapter, redact_secrets
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
# 3. Provider <-> Model Binding Tests (Requirement 2)
# ==========================================

def test_provider_model_binding_valid_combination():
    routing = RoutingPolicy()
    decision = routing.resolve_route("gpt-5.6-luna", requested_provider="openai")
    assert decision.primary_provider == "openai"
    assert decision.primary_model == "gpt-5.6-luna"

    gemini_decision = routing.resolve_route("gemini-3.6-flash", requested_provider="google")
    assert gemini_decision.primary_provider == "google"

    claude_decision = routing.resolve_route("claude-opus-4-7", requested_provider="anthropic")
    assert claude_decision.primary_provider == "anthropic"


def test_provider_model_binding_mismatches_rejected():
    routing = RoutingPolicy()

    # gpt model + anthropic provider -> reject
    with pytest.raises(ProviderModelMismatchError) as exc_info:
        routing.resolve_route("gpt-5.6-luna", requested_provider="anthropic")
    assert "Provider mismatch" in exc_info.value.detail
    assert "anthropic" in exc_info.value.detail

    # gemini model + openai provider -> reject
    with pytest.raises(ProviderModelMismatchError) as exc_info:
        routing.resolve_route("gemini-3.6-flash", requested_provider="openai")
    assert "Provider mismatch" in exc_info.value.detail
    assert "openai" in exc_info.value.detail

    # claude model + google provider -> reject
    with pytest.raises(ProviderModelMismatchError) as exc_info:
        routing.resolve_route("claude-opus-4-7", requested_provider="google")
    assert "Provider mismatch" in exc_info.value.detail
    assert "google" in exc_info.value.detail


def test_routing_policy_capability_validation():
    reg = ModelRegistry()
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
# 4. Mock Provider Environment Safety Tests (Requirement 3)
# ==========================================

def test_mock_provider_environment_guard_production_rejected():
    prod_settings = Settings(app_env="production", allow_mock_provider=False)
    with patch("app.services.gateway.provider_registry.get_settings", return_value=prod_settings):
        # Provider registry must register mock as disabled
        reg = ProviderRegistry()
        assert not reg.is_enabled("mock")
        with pytest.raises(ProviderDisabledError):
            reg.require_adapter("mock")

        # Credential resolver must also reject mock
        db = FakeDBSession()
        resolver = CredentialResolver(db)
        with pytest.raises(ProviderDisabledError):
            resolver.resolve("mock", uuid.uuid4())


def test_mock_provider_environment_guard_staging_policy():
    # Staging with allow_mock_provider=False
    staging_no_mock = Settings(app_env="staging", allow_mock_provider=False)
    with patch("app.services.gateway.provider_registry.get_settings", return_value=staging_no_mock):
        reg = ProviderRegistry()
        assert not reg.is_enabled("mock")

    # Staging with allow_mock_provider=True
    staging_with_mock = Settings(app_env="staging", allow_mock_provider=True)
    with patch("app.services.gateway.provider_registry.get_settings", return_value=staging_with_mock):
        reg = ProviderRegistry()
        assert reg.is_enabled("mock")


def test_mock_provider_environment_guard_test_allowed():
    test_settings = Settings(app_env="test", allow_mock_provider=False)
    with patch("app.services.gateway.provider_registry.get_settings", return_value=test_settings):
        reg = ProviderRegistry()
        assert reg.is_enabled("mock")
        assert reg.require_adapter("mock") is not None


# ==========================================
# 5. Credential Resolver & Tenant Boundary Tests (Requirement 1)
# ==========================================

class FakeDBSession:
    def __init__(self, cred_row=None):
        self.cred_row = cred_row

    def scalar(self, statement):
        return self.cred_row


def test_credential_resolver_cross_tenant_access_rejected():
    db = FakeDBSession()
    resolver = CredentialResolver(db)
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    user_tenant_a = SimpleNamespace(agency_id=tenant_a)

    # Attempting to access tenant_b's credential with user belonging to tenant_a must raise TenantSecurityError
    with pytest.raises(TenantSecurityError) as exc_info:
        resolver.resolve("openai", tenant_b, user=user_tenant_a)
    assert "Principal agency does not match requested tenant context" in exc_info.value.detail


def test_credential_resolver_missing_credential_raises():
    db = FakeDBSession(cred_row=None)
    resolver = CredentialResolver(db)
    agency_id = uuid.uuid4()

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(CredentialResolutionError):
            resolver.resolve("openai", agency_id)


# ==========================================
# 6. Fallback Semantics Tests (Requirement 7)
# ==========================================

@pytest.mark.asyncio
async def test_gateway_no_fallback_on_tenant_security_error():
    db = FakeDBSession()
    mock_adapter = MockProviderAdapter()
    provider_reg = ProviderRegistry([mock_adapter])
    model_reg = ModelRegistry()

    gateway = AIGateway(
        db=db,
        provider_registry=provider_reg,
        model_registry=model_reg,
    )

    tenant_1 = uuid.uuid4()
    tenant_2 = uuid.uuid4()
    user_1 = SimpleNamespace(agency_id=tenant_1)
    messages = [GatewayMessage(role="user", content="Hi")]

    # Cross-tenant violation must raise TenantSecurityError immediately without falling back
    with pytest.raises(TenantSecurityError):
        await gateway.complete(
            agency_id=tenant_2,
            user=user_1,
            model="mock-fast",
            messages=messages,
            allow_fallback=True,
        )


@pytest.mark.asyncio
async def test_gateway_no_fallback_on_provider_model_mismatch():
    db = FakeDBSession()
    gateway = AIGateway(db=db)
    tenant = uuid.uuid4()
    user = SimpleNamespace(agency_id=tenant)
    messages = [GatewayMessage(role="user", content="Hi")]

    # Mismatch between requested provider and model must fail fast without fallback
    with pytest.raises(ProviderModelMismatchError):
        await gateway.complete(
            agency_id=tenant,
            user=user,
            model="gpt-5.6-luna",
            provider="anthropic",
            messages=messages,
            allow_fallback=True,
        )


@pytest.mark.asyncio
async def test_gateway_fallback_on_genuine_provider_execution_failure():
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
    messages = [GatewayMessage(role="user", content="Hello")]

    with pytest.raises(ProviderExecutionError):
        await gateway.complete(
            agency_id=agency_id,
            user=user,
            model="mock-fast",
            messages=messages,
            allow_fallback=True,
        )


# ==========================================
# 7. Secret Redaction Tests (Requirement 5)
# ==========================================

def test_secret_redaction_utility():
    secret_key = "AIzaSySecretApiKey123456"
    test_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={secret_key}"

    redacted = redact_secrets(test_url, secret_key)
    assert secret_key not in redacted
    assert "[REDACTED" in redacted

    error_msg = f"HTTP 403 request failed for {test_url} with key={secret_key}"
    redacted_error = redact_secrets(error_msg, secret_key)
    assert secret_key not in redacted_error


@pytest.mark.asyncio
async def test_google_adapter_error_redacts_credentials():
    adapter = GoogleGeminiAdapter()
    secret_key = "AIzaSyVerySecretKey999"
    cred = ResolvedCredential(
        provider_id="google",
        api_key=secret_key,
        base_url="https://generativelanguage.googleapis.com/v1beta",
        source="agency_byok",
    )

    # Simulate HTTP 403 response containing URL with key
    mock_response = httpx.Response(
        status_code=403,
        json={"error": {"message": f"API key {secret_key} invalid on URL ?key={secret_key}"}},
        request=httpx.Request("GET", f"https://mock.url?key={secret_key}"),
    )

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        with pytest.raises(ProviderExecutionError) as exc_info:
            await adapter.test_connection(cred)

        assert secret_key not in exc_info.value.detail
        assert "[REDACTED" in exc_info.value.detail


# ==========================================
# 8. Provider Connection Verification Tests (Requirement 6)
# ==========================================

@pytest.mark.asyncio
async def test_openai_test_connection_success_and_failure():
    adapter = OpenAIAdapter()
    cred = ResolvedCredential("openai", "sk-test", "https://api.openai.com/v1", "agency_byok")

    # 1. Success case
    success_resp = httpx.Response(
        200,
        json={"data": [{"id": "gpt-5.6-luna"}, {"id": "gpt-5.6-terra"}]},
        request=httpx.Request("GET", "https://api.openai.com/v1/models"),
    )
    with patch("httpx.AsyncClient.get", return_value=success_resp):
        res = await adapter.test_connection(cred)
        assert res["ok"] is True
        assert "gpt-5.6-luna" in res["models"]

    # 2. HTTP 401 error case -> must raise ProviderExecutionError
    fail_resp = httpx.Response(
        401,
        json={"error": {"message": "Incorrect API key provided"}},
        request=httpx.Request("GET", "https://api.openai.com/v1/models"),
    )
    with patch("httpx.AsyncClient.get", return_value=fail_resp):
        with pytest.raises(ProviderExecutionError):
            await adapter.test_connection(cred)

    # 3. Network error -> must raise ProviderExecutionError
    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Network unreachable")):
        with pytest.raises(ProviderExecutionError):
            await adapter.test_connection(cred)


@pytest.mark.asyncio
async def test_anthropic_test_connection_success_and_failure():
    adapter = AnthropicAdapter()
    cred = ResolvedCredential("anthropic", "sk-ant-test", "https://api.anthropic.com/v1", "agency_byok")

    # 1. Success case
    success_resp = httpx.Response(
        200,
        json={"data": [{"id": "claude-opus-4-7"}, {"id": "claude-sonnet-4-6"}]},
        request=httpx.Request("GET", "https://api.anthropic.com/v1/models"),
    )
    with patch("httpx.AsyncClient.get", return_value=success_resp):
        res = await adapter.test_connection(cred)
        assert res["ok"] is True
        assert "claude-opus-4-7" in res["models"]

    # 2. HTTP 401 error case -> must raise ProviderExecutionError, never return ok: True!
    fail_resp = httpx.Response(
        401,
        json={"error": {"message": "Invalid x-api-key"}},
        request=httpx.Request("GET", "https://api.anthropic.com/v1/models"),
    )
    with patch("httpx.AsyncClient.get", return_value=fail_resp):
        with pytest.raises(ProviderExecutionError):
            await adapter.test_connection(cred)

    # 3. Network error -> must raise ProviderExecutionError
    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectTimeout("Timed out")):
        with pytest.raises(ProviderExecutionError):
            await adapter.test_connection(cred)


@pytest.mark.asyncio
async def test_google_test_connection_success_and_failure():
    adapter = GoogleGeminiAdapter()
    cred = ResolvedCredential("google", "ai-key", "https://generativelanguage.googleapis.com/v1beta", "agency_byok")

    # 1. Success case
    success_resp = httpx.Response(
        200,
        json={"models": [{"name": "models/gemini-3.6-flash"}, {"name": "models/gemini-3.5-flash"}]},
        request=httpx.Request("GET", "https://generativelanguage.googleapis.com/v1beta/models"),
    )
    with patch("httpx.AsyncClient.get", return_value=success_resp):
        res = await adapter.test_connection(cred)
        assert res["ok"] is True
        assert "gemini-3.6-flash" in res["models"]

    # 2. Failure case (400 / 403) -> must raise ProviderExecutionError
    fail_resp = httpx.Response(
        400,
        json={"error": {"message": "API key not valid"}},
        request=httpx.Request("GET", "https://generativelanguage.googleapis.com/v1beta/models"),
    )
    with patch("httpx.AsyncClient.get", return_value=fail_resp):
        with pytest.raises(ProviderExecutionError):
            await adapter.test_connection(cred)


# ==========================================
# 9. Response Normalization Tests
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
