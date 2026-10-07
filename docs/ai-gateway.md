# Phase 2 — Provider + Model Abstraction / AI Gateway

## Architecture Overview

The InnoTech AI Gateway delivers a production, provider-neutral foundation separating model execution from application and agent workflows.

```
Agent / Studio / Application
            ↓
        AIGateway
            ↓
       RoutingPolicy
            ↓
    CredentialResolver
            ↓
     ProviderAdapter
            ↓
 OpenAI / Anthropic / Gemini / Mock
            ↓
    Normalized Response
```

---

## Components

### 1. ProviderAdapter (`app.services.gateway.base_adapter`)
Canonical abstract base class requiring:
- `provider_id`: Unique string ID (`openai`, `anthropic`, `google`, `mock`).
- `capabilities()`: Declares `supports_tools`, `supports_vision`, `supports_streaming`, `supports_structured_output`.
- `list_models()`: Discovered or supported model IDs.
- `chat()`: Async execution receiving `ResolvedCredential`, model, `GatewayMessage` list, and `ToolDefinition` list.
- `normalize_response()`: Transforms provider raw outputs into normalized `GatewayResponse` and `GatewayUsage`.
- `test_connection()`: Validates provider credentials.

Implemented Adapters:
- `OpenAIAdapter`: Supports OpenAI chat completions & Responses API, plus OpenRouter proxy compatibility.
- `AnthropicAdapter`: Supports Anthropic Claude Messages API.
- `GoogleGeminiAdapter`: Supports Google Gemini REST Generative Language API.
- `MockProviderAdapter`: Deterministic testing adapter with full configurable responses and tool calls.

### 2. ProviderRegistry (`app.services.gateway.provider_registry`)
Central registry for provider adapters:
- `register(adapter, enabled=True)`: Registers provider adapters.
- `get_adapter(provider_id)` / `require_adapter(provider_id)`: Adapter lookup with enabled-state validation.
- `is_enabled(provider_id)` / `set_enabled(provider_id, enabled)`: Dynamic enable/disable control.
- `list_providers()`: Discovers registered providers and their metadata.

### 3. ModelRegistry (`app.services.gateway.model_registry`)
Centralized catalog of AI models and operational constraints:
- `model_id`, `provider_id`, `display_name`, `family`
- `context_window`, `max_output_tokens`
- `capabilities` (`supports_tools`, `supports_vision`, `supports_streaming`, `supports_structured_output`)
- `input_price_per_1k`, `output_price_per_1k`
- `active`, `badge`, `note`, `metadata`

### 4. CredentialResolver (`app.services.gateway.credential_resolver`)
Enforces server-side tenant isolation (Phase 1):
- Resolves encrypted `ProviderCredential` from database for tenant (`agency_id`).
- Verifies that calling principal (`User`) matches requested `agency_id`.
- Rejects frontend-supplied keys.
- Prevents SSRF: base URLs must match strictly trusted server-configured domains.
- Never logs or exposes plaintext API keys.

### 5. RoutingPolicy (`app.services.gateway.routing`)
Deterministic server-side routing:
- Maps model request to primary provider and model.
- Validates required capabilities (e.g., tools or vision) against model definitions.
- Chooses deterministic fallback within model family if primary fails.

### 6. AIGateway (`app.services.gateway.gateway`)
Unified service boundary:
- Validates principal and tenant boundaries.
- Resolves routing decision through `RoutingPolicy`.
- Resolves provider credential through `CredentialResolver`.
- Dispatches execution to `ProviderAdapter`.
- Intercepts provider failures and executes policy-controlled fallback when permitted.
- Returns normalized `GatewayResponse` with `GatewayUsage`.

---

## Adding a New Provider

1. Implement `BaseProviderAdapter` in `app/services/gateway/adapters/<provider>_adapter.py`:
   - Implement `chat()`, `normalize_response()`, and `test_connection()`.
2. Register the adapter in `ProviderRegistry`:
   ```python
   registry.register(MyNewProviderAdapter(), enabled=True)
   ```
3. Register supported models in `ModelRegistry` with appropriate `ModelCapability`.
4. Add provider credential mapping in `CredentialResolver` if applicable.

---

## Migrated vs. Legacy AI Paths

- **Migrated Path:**
  - `POST /api/studio/{client_id}/agents/{agent_id}/preview`: Fully routed through `AIGateway` with tenant verification, capability validation, and policy fallback.
- **Legacy Paths Kept Temporarily for Stability:**
  - `app.services.tools.runner.run_completion`
  - `app.services.social_worker`
  - `app.services.execution_dispatch`
  - `app.routers.studio_simulation`
  - *Reason:* Phase 2 focuses on establishing the gateway foundation and safely integrating initial execution paths without disrupting active WhatsApp and social workers. These workers will be migrated to `AIGateway` in subsequent scheduled phases.
