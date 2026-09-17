# InnoTech AI Agent Factory — Production SaaS Strategy

**Status:** Authoritative implementation strategy / future reference
**Repository:** `innotechat/ai-agent-factory`
**Upstream basis:** Voysse-derived codebase
**Target:** Production-grade, scalable, multi-tenant, white-label AI Agent SaaS + OpenAI-compatible AI platform

---

## 0. Purpose of this document

This document is the long-term architectural and product reference for transforming the current Voysse-derived application into an InnoTech-operated SaaS platform.

It is intentionally more than a rebranding checklist. Future implementation work MUST use this document to preserve the target architecture and avoid local fixes that move the codebase away from the production design.

### Core product vision

Build one platform that can serve:

1. Free direct users.
2. Paid direct customers.
3. Agencies and resellers.
4. Enterprise customers.
5. White-label partners operating the platform under their own brand.
6. Developers consuming agents through an OpenAI-compatible API.

The product should ultimately be a platform, not merely a WhatsApp chatbot dashboard.

---

# 1. Target product model

The final hierarchy is:

```text
InnoTech Platform
    |
    +-- Direct Customer Tenant
    |      +-- Users / Team
    |      +-- Agents
    |      +-- Knowledge
    |      +-- Channels
    |      +-- API Keys
    |      +-- Usage / Billing
    |
    +-- Agency / Reseller Tenant
           +-- Agency Team
           +-- Client Tenant / Workspace
           |      +-- Agents
           |      +-- Knowledge
           |      +-- Channels
           |      +-- Portal
           +-- Usage / Billing
           +-- White-label Branding
           +-- Custom Domains
```

The existing Agency -> Client -> Agent model is useful as a migration starting point, but the long-term platform must support tenant types and reusable tenant infrastructure.

---

# 2. Non-negotiable architectural principles

These rules apply to all future implementation work.

## 2.1 Multi-tenancy first

Every business object must have a clear ownership boundary. Never rely on frontend filtering for tenant isolation.

Use centralized request context:

```text
request
  -> authentication
  -> principal
  -> tenant
  -> role / permissions
  -> plan / entitlements
  -> quota
```

## 2.2 Provider-neutral core

Business logic must never be tightly coupled to OpenAI, Anthropic, Gemini, or any single AI vendor.

Use adapters:

```text
AI Provider Interface
  +-- OpenAI Adapter
  +-- Anthropic Adapter
  +-- Gemini Adapter
  +-- OpenRouter Adapter
  +-- Custom OpenAI-Compatible Adapter
  +-- Future providers
```

## 2.3 Platform-managed AI + BYOK

Both modes must be first-class:

```text
Managed AI:
Customer -> InnoTech -> provider account

BYOK:
Customer -> InnoTech -> customer provider credential
```

Free and normal paid plans should not require users to own provider API keys.

Enterprise and advanced users may use BYOK.

## 2.4 Entitlements, not plan-name conditionals

Do not implement business access as scattered code such as:

```python
if plan == "pro":
```

Use feature and quota entitlements:

```text
api.enabled
whatsapp.enabled
custom_domain.enabled
agents.max
messages.monthly
```

## 2.5 API-first

The web UI is one client of the platform. The API must be capable of operating independently.

## 2.6 Horizontal scalability

Do not assume one API process, one worker, one WhatsApp process, or local filesystem persistence.

## 2.7 Secrets never leave the server

Provider keys, API secrets, webhook secrets, OAuth secrets and channel credentials must never be returned in plaintext after storage.

## 2.8 Compatibility before destructive migration

Do not rename tables, packages, environment variables, or public endpoints merely for aesthetics if doing so creates unnecessary migration risk. Introduce compatibility layers and migrate deliberately.

## 2.9 Observability is part of the product

Every AI request, provider call, job and important channel event needs correlation IDs and usage/cost metadata.

## 2.10 No speculative rewrites

Preserve working functionality. Refactor only where required by the target architecture, security, scale, or maintainability.

---

# 3. Current repository baseline

The current repository already contains a substantial foundation:

```text
apps/api       FastAPI / SQLAlchemy / Alembic
apps/web       Next.js / React / TypeScript / Tailwind
apps/whatsapp  Node.js / Baileys
apps/marketing Marketing application
apps/docs      Documentation application
PostgreSQL
Docker Compose
```

Existing product concepts include agencies, users/team, clients, agents, knowledge, custom tools, MCP, WhatsApp, web widget, inbox, client portal, custom domains, AI providers and Studio functionality.

This foundation should be evolved rather than discarded.

---

# 4. Rebranding strategy

Rebranding MUST be systematic.

## 4.1 Display brand

Replace visible Voysse identity with the final InnoTech product identity.

Target working name:

**InnoTech AI Agent Factory**

The final commercial name can be changed later without changing the architecture.

## 4.2 Legacy identifiers

Search the complete repository for:

```text
Voysse
voysse
voysse.cl
openvoiss
OpenVoiss
old domains
old documentation URLs
old email addresses
old Docker/container names
old database defaults
```

Classify each occurrence as:

- display text
- documentation
- URL
- environment variable
- database identifier
- code compatibility identifier
- test fixture
- external integration

Do not blindly replace every occurrence.

## 4.3 Brand configuration

Create a central brand configuration layer rather than hard-coding brand values throughout the UI.

Minimum settings:

```text
brand_name
logo
favicon
primary_color
secondary_color
accent_color
login_background
support_email
support_url
terms_url
privacy_url
powered_by_mode
hide_platform_brand
```

---

# 5. White-label architecture

White-label must operate at tenant level.

## 5.1 BrandSettings

Recommended model:

```text
brand_settings
----------------
id
tenant_id
brand_name
legal_name
logo_asset_id
favicon_asset_id
primary_color
secondary_color
accent_color
font_family
login_background_asset_id
email_from_name
email_from_address
support_email
support_url
terms_url
privacy_url
hide_platform_brand
powered_by_mode
custom_css
created_at
updated_at
```

## 5.2 Domains

Use a dedicated domain model instead of embedding domain state into unrelated records.

```text
domains
----------------
id
tenant_id
domain
type
status
verification_token
verified_at
ssl_status
is_primary
created_at
updated_at
```

Support:

```text
agency.innotech.example
client.customer.com
ai.customer.com
```

DNS verification must precede production routing.

## 5.3 White-label layers

Support progressively:

1. Logo/colors/name.
2. Custom domain.
3. Custom login/portal.
4. Custom widget branding.
5. Custom emails.
6. API branding/tenant identity.
7. Remove platform branding for eligible plans.
8. Reseller hierarchy.

---

# 6. Tenant and identity model

Long-term canonical entity should be `Tenant` / `Organization`.

Possible tenant types:

```text
direct_customer
agency
reseller
enterprise
internal
```

Existing Agency records can initially remain physically named `agencies` for compatibility. Introduce the new abstraction before a database rename.

Recommended concepts:

```text
tenants
users
memberships
roles
permissions
api_keys
sessions
audit_logs
```

A user must not be globally interpreted as an administrator simply because the current code was designed around an agency admin.

Replace the current admin-centric access dependency with reusable authorization primitives:

```text
get_current_principal()
get_current_tenant()
require_role(...)
require_permission(...)
require_scope(...)
require_feature(...)
require_quota(...)
```

---

# 7. RBAC and permissions

Roles should be configurable and permission-driven.

Initial roles:

```text
platform_owner
platform_admin
reseller_owner
agency_owner
admin
manager
operator
developer
client_admin
client_operator
viewer
```

Permissions examples:

```text
agents.read
agents.write
knowledge.read
knowledge.write
channels.manage
billing.read
billing.manage
team.manage
branding.manage
domains.manage
api.manage
usage.read
```

Never trust a role supplied by the browser.

---

# 8. Public API strategy

The platform must expose a stable `/v1` API.

Initial compatibility targets:

```text
GET  /v1/models
POST /v1/chat/completions
POST /v1/responses
POST /v1/embeddings
POST /v1/audio/transcriptions
```

The exact supported surface should be implemented based on the actual provider adapters and test suite rather than pretending unsupported endpoints work.

## 8.1 OpenAI-compatible client experience

Target usage:

```python
from openai import OpenAI

client = OpenAI(
    api_key="tenant_api_key",
    base_url="https://api.example.com/v1",
)

response = client.chat.completions.create(
    model="sales-agent",
    messages=[
        {"role": "user", "content": "Hello"}
    ],
)
```

The client should not need to know which underlying provider executes the request.

## 8.2 Agent-native API

In addition to model compatibility, expose a native Agent API where useful:

```text
/v1/agents
/v1/agents/{agent_id}
/v1/agents/{agent_id}/responses
/v1/agents/{agent_id}/knowledge
/v1/agents/{agent_id}/tools
```

The native API should expose platform concepts that a raw model API cannot express.

---

# 9. API authentication

Implement API keys as hashed secrets.

Recommended structure:

```text
api_keys
----------------
id
tenant_id
name
key_prefix
secret_hash
scopes
last_used_at
expires_at
revoked_at
created_at
```

Only a safe prefix is stored for display.

Support:

- scoped keys
- expiration
- revocation
- rotation
- last-used tracking
- audit logging
- optional IP restrictions for enterprise

Add idempotency support for mutation APIs where duplicate execution could be harmful.

---

# 10. AI provider architecture

Replace the current small provider registry with a proper provider abstraction.

Target:

```text
ProviderRegistry
ModelRegistry
ProviderAdapter
RoutingPolicy
CredentialResolver
UsageNormalizer
CostCalculator
CircuitBreaker
```

Provider adapters:

```text
OpenAI
Anthropic
Gemini
OpenRouter
Custom OpenAI-Compatible
Azure OpenAI
Future providers
```

Do not add providers by scattering conditionals through the AI service.

---

# 11. Model catalog

Create a central model catalog.

```text
models
----------------
id
provider_id
external_model_id
display_name
capabilities
context_window
input_price
output_price
status
metadata
created_at
updated_at
```

Capabilities should include:

```text
text
vision
audio_input
audio_output
tools
structured_output
embeddings
reasoning
streaming
```

Tenant access can be controlled separately:

```text
tenant_model_access
----------------
tenant_id
model_id
enabled
priority
custom_price
```

---

# 12. Routing engine

Agents should be able to use logical model policies rather than being permanently tied to a vendor.

Examples:

```text
fast
balanced
premium
cheap
vision
coding
custom
```

Routing pipeline:

```text
request
 -> tenant
 -> plan
 -> agent
 -> policy
 -> eligible models
 -> provider health
 -> cost policy
 -> model selection
 -> execution
 -> usage normalization
```

Routing decisions must be deterministic and auditable.

---

# 13. Managed AI / BYOK credential strategy

Credentials can exist at different scopes in the final system:

```text
platform provider credential
reseller credential
tenant credential
agent override credential (enterprise only if needed)
```

Do not expose decrypted credentials through API responses or logs.

Provider credentials should remain encrypted at rest.

For larger production deployments, evaluate an external secrets manager rather than relying indefinitely on application-level encryption keys.

---

# 14. Agent Runtime

The Agent Runtime is the core product abstraction.

An agent consists of:

```text
identity
instructions
personality
business context
knowledge
memory policy
tools
MCP tools
model policy
channel configuration
handoff policy
safety policy
usage policy
```

Runtime pipeline:

```text
Inbound event
  -> identify tenant/client/agent
  -> authenticate channel
  -> load agent configuration
  -> load memory
  -> retrieve knowledge
  -> resolve tools
  -> resolve model
  -> reserve quota/credits
  -> execute provider
  -> execute tools if needed
  -> settle actual usage
  -> persist response
  -> emit events
```

Keep this pipeline provider-neutral.

---

# 15. Free and paid plans

Free access is a first-class product mode, not a special developer environment.

Initial plan families may be:

```text
FREE
STARTER
PRO
BUSINESS
AGENCY
ENTERPRISE
```

Exact pricing and limits MUST be calculated from actual provider costs and business requirements before production launch.

Do not hard-code arbitrary limits permanently.

---

# 16. Entitlement engine

Create feature and quota definitions.

Examples:

```text
agents.max
team_members.max
messages.monthly
api.enabled
api.requests.monthly
whatsapp.enabled
instagram.enabled
custom_domain.enabled
white_label.enabled
mcp.enabled
custom_tools.enabled
advanced_models.enabled
analytics.enabled
storage.gb
```

Runtime checks:

```python
require_feature("api.enabled")
require_quota("messages.monthly", amount=1)
```

The same entitlement system must be usable by API, web UI and workers.

---

# 17. Usage and metering

Every billable AI operation must create a normalized usage event.

```text
usage_events
----------------
id
request_id
tenant_id
user_id
agent_id
provider
model
operation
input_tokens
output_tokens
audio_seconds
image_units
tool_calls
estimated_cost
billable_units
metadata
created_at
```

Add aggregation tables:

```text
usage_hourly
usage_daily
usage_monthly
```

Do not calculate historical dashboards by scanning raw events on every request.

---

# 18. Credit ledger

Use an auditable ledger rather than a mutable integer-only balance.

```text
credit_accounts
credit_ledger
credit_reservations
credit_settlements
```

Flow:

```text
request
 -> pre-flight quota check
 -> atomic reservation
 -> provider execution
 -> actual usage
 -> settlement
 -> release unused reservation
```

This is especially important for concurrency and paid usage.

The existing InnoTech SaaS Core AI credit accounting concepts should be reused where technically compatible rather than duplicated.

---

# 19. Billing architecture

Billing must remain separate from Agent Runtime.

Core entities:

```text
plans
plan_features
subscriptions
subscription_items
invoices
payments
payment_events
credits
```

Payment integration should use an adapter:

```text
PaymentProvider
  +-- Stripe
  +-- Razorpay
  +-- Cashfree
  +-- future providers
```

All payment state changes must be webhook-driven and idempotent.

---

# 20. Reseller architecture

This is a strategic requirement for the white-label business model.

A reseller must be able to:

```text
create customers
invite customers
assign plans
create agents
manage branding
configure domains
see customer usage
manage customer channels
```

But a reseller must never be able to access another reseller's tenants.

Target:

```text
Platform
  -> Reseller A
      -> Customer 1
      -> Customer 2
  -> Reseller B
      -> Customer 3
      -> Customer 4
```

Tenant ancestry and authorization must be enforced server-side.

---

# 21. Channel architecture

Channels should be adapters around the Agent Runtime.

```text
Agent Runtime
  +-- Web Widget
  +-- WhatsApp Cloud
  +-- WhatsApp Session/Baileys
  +-- Instagram
  +-- Facebook Messenger
  +-- API
  +-- future channels
```

A channel must not contain business logic that belongs in the Agent Runtime.

---

# 22. WhatsApp scalability

Baileys is stateful. Do not make the main API responsible for persistent WhatsApp sessions.

Target:

```text
API
 |
 +-- WhatsApp Cloud integration
 |
 +-- WhatsApp Session Service
          |
          +-- session workers
          +-- encrypted session state
```

Session routing must be tenant/client/channel aware.

The architecture must allow multiple workers/instances.

---

# 23. Queue and worker architecture

Long-running work must not block API requests.

Use a queue abstraction for:

```text
document processing
embeddings
AI background work
audio processing
webhook processing
WhatsApp events
email
usage aggregation
billing events
domain verification
analytics
```

Initial production stack can use Redis-backed jobs where appropriate. The queue interface should not make the rest of the application dependent on one queue vendor.

---

# 24. Storage architecture

Do not depend on local application disk for durable SaaS data.

Use object storage for:

```text
logos
knowledge documents
attachments
audio
images
exports
backups where applicable
```

Potential backends:

```text
S3
Cloudflare R2
MinIO for self-hosted deployments
```

Database stores metadata and object identifiers.

---

# 25. Database strategy

PostgreSQL remains the primary transactional database.

Rules:

1. Every migration must be reversible where practical.
2. Add indexes based on actual query paths.
3. Foreign keys must enforce ownership relationships.
4. High-volume event tables need retention/partition strategy when scale requires it.
5. Never silently delete tenant data as part of routine billing or lifecycle operations.
6. Tenant deletion must have an explicit, auditable workflow.

For very large tenants, evaluate database partitioning and/or tenant-aware sharding only after measurement demonstrates the need.

---

# 26. Security architecture

Minimum production controls:

```text
TLS everywhere
secure cookies
CSRF protection where applicable
short-lived access tokens
session revocation
API key hashing
secret encryption
RBAC
permission checks
rate limiting
quota enforcement
SSRF protection
webhook signature verification
idempotency
audit logging
security headers
input validation
output filtering where needed
file upload restrictions
malware scanning strategy for untrusted files
```

Never log:

```text
API keys
passwords
session tokens
webhook secrets
provider credentials
full authorization headers
```

---

# 27. SSRF and custom tools

The existing custom HTTP tool capability is security-sensitive.

Keep the SSRF guard and strengthen it before allowing arbitrary customers to use the feature.

Controls should include:

- block loopback
- block private networks by default
- block link-local addresses
- validate DNS resolution
- protect against DNS rebinding where practical
- enforce HTTP method policy
- enforce timeout
- response-size limit
- redirect policy
- protocol allowlist
- optional enterprise allowlist

MCP servers require equivalent outbound security considerations.

---

# 28. Observability

Every request should carry:

```text
request_id
trace_id
tenant_id
user_id
agent_id
channel
provider
model
```

Capture:

```text
latency
status
provider latency
tokens
estimated cost
queue latency
error category
retry count
```

Metrics should include:

```text
API requests/sec
error rate
P95/P99 latency
provider error rate
provider latency
queue depth
worker utilization
active tenants
active agents
AI spend
credit usage
WhatsApp sessions
```

---

# 29. Feature flags

Introduce platform/tenant feature flags.

Use cases:

```text
new provider
new billing system
new channel
beta agent runtime
new UI
enterprise-only capability
migration rollout
```

Feature flags must be evaluated server-side for security-sensitive capabilities.

---

# 30. Platform admin control plane

The final platform admin should provide:

```text
Overview
Tenants
Users
Resellers
Plans
Subscriptions
Usage
Credits
Revenue
AI Providers
Models
Domains
Channels
Jobs
System Health
Feature Flags
Audit Logs
Security / Abuse
```

Admin actions should be auditable.

Dangerous actions require confirmation and, where appropriate, re-authentication.

---

# 31. Customer dashboard

Customer workspace:

```text
Dashboard
Agents
Knowledge
Inbox
Channels
Tools
MCP
Playground
API
Usage
Billing
Team
Branding
Domains
Settings
```

Navigation must be entitlement-aware but server authorization remains authoritative.

---

# 32. Reseller dashboard

Reseller workspace:

```text
Dashboard
Customers
Agents
Templates
Usage
Revenue / Billing
Team
Branding
Domains
API
Settings
```

A reseller sees only its authorized customer tree.

---

# 33. Developer experience

Publish:

```text
API reference
OpenAPI specification
SDK examples
curl examples
Python examples
JavaScript examples
webhook documentation
rate-limit documentation
error documentation
```

API errors should have stable machine-readable codes.

Example:

```json
{
  "error": {
    "code": "quota_exceeded",
    "message": "Monthly message quota exceeded",
    "request_id": "..."
  }
}
```

---

# 34. API versioning

Use:

```text
/v1
/v2
```

Do not break `/v1` casually.

Provider-specific changes should not automatically become public API breaking changes.

Maintain compatibility tests for the public API.

---

# 35. Deployment architecture

Development:

```text
Docker Compose
PostgreSQL
Redis
API
Web
Workers
WhatsApp
```

Production starting architecture:

```text
CDN / Edge
    |
Load Balancer / Gateway
    |
+---+--------------------+
|                        |
API replicas         Web replicas
|
+-- Queue -> Worker replicas
|
+-- PostgreSQL
+-- Redis
+-- Object Storage
+-- WhatsApp services
```

The architecture must support multiple API replicas without relying on process memory for shared state.

---

# 36. Environment configuration

Separate configuration into:

```text
application config
provider config
security config
storage config
queue config
billing config
channel config
observability config
```

Production must fail fast on missing critical secrets.

Development defaults must never accidentally become production defaults.

---

# 37. Testing strategy

Every major phase must add tests before declaring completion.

## Unit

Provider adapters, authorization, entitlement checks, usage calculations, parsers.

## Integration

Database, queue, storage, provider mocks, webhook validation.

## API contract

OpenAI-compatible endpoints and native Agent API.

## Tenant isolation

Explicit cross-tenant access tests are mandatory.

## Security

SSRF, auth bypass, privilege escalation, secret leakage, malformed webhooks, file uploads.

## End-to-end

Signup -> plan -> agent -> knowledge -> channel -> conversation -> usage -> billing.

## Load

API concurrency, agent execution, provider latency, queue throughput and WebSocket/channel behavior.

---

# 38. CI/CD quality gates

A production merge should require:

```text
lint
format checks
type checks
unit tests
integration tests
migration checks
API contract tests
security checks
build
container build
```

Do not declare a phase complete because the application builds alone.

---

# 39. Migration strategy from the current repository

Migration must be incremental.

### Step 1
Freeze a verified baseline.

### Step 2
Add centralized tenant/request context.

### Step 3
Add RBAC/permissions without breaking existing admin flows.

### Step 4
Add provider abstraction behind the existing AI service.

### Step 5
Add model registry.

### Step 6
Add managed credentials + BYOK resolution.

### Step 7
Add public API keys and `/v1` API.

### Step 8
Add usage events.

### Step 9
Add credit reservations/settlement.

### Step 10
Add plans and entitlements.

### Step 11
Add billing.

### Step 12
Upgrade white-label branding/domain architecture.

### Step 13
Add reseller hierarchy.

### Step 14
Move durable files to object storage.

### Step 15
Harden queue/workers and WhatsApp scaling.

### Step 16
Production observability and load testing.

### Step 17
Only then perform optional database/package renames.

---

# 40. Phase execution roadmap

## Phase 0 — Audit and baseline

Deliverables:

- complete repository inventory
- upstream/license review
- dependency map
- provider coupling map
- database ownership map
- auth/RBAC map
- current API inventory
- current UI branding inventory
- current test baseline

Exit criteria:

- no major unknown subsystem before refactor begins
- clean baseline build/test status recorded

## Phase 1 — Rebrand foundation

Deliverables:

- InnoTech branding
- centralized brand config
- environment cleanup
- documentation migration
- compatibility-safe legacy identifier handling

## Phase 2 — SaaS identity and tenancy

Deliverables:

- tenant abstraction
- memberships
- permissions
- request context
- API key foundation
- audit log

## Phase 3 — AI Gateway

Deliverables:

- provider interface
- adapters
- model registry
- routing
- managed AI
- BYOK
- provider health/circuit breaking

## Phase 4 — Public API

Deliverables:

- `/v1/models`
- `/v1/chat/completions`
- `/v1/responses`
- embeddings/audio where implemented
- API key scopes
- API documentation
- compatibility tests

## Phase 5 — Usage and Credits

Deliverables:

- usage events
- normalized provider usage
- credit ledger
- reservation/settlement
- quotas
- usage dashboards

## Phase 6 — Plans and Billing

Deliverables:

- plans
- entitlements
- subscriptions
- invoices
- payment adapters
- webhook idempotency

## Phase 7 — White-label

Deliverables:

- BrandSettings
- custom domains
- custom login
- email branding
- widget branding
- powered-by controls

## Phase 8 — Reseller platform

Deliverables:

- reseller tenant type
- customer management
- customer hierarchy
- reseller billing/usage
- reseller branding

## Phase 9 — Scale and infrastructure

Deliverables:

- Redis/queue hardening
- worker scaling
- object storage
- WhatsApp session service scaling
- observability
- load tests
- backup/recovery

## Phase 10 — Production certification

Deliverables:

- security audit
- tenant isolation audit
- API compatibility certification
- disaster recovery test
- migration rehearsal
- billing reconciliation test
- load test report
- launch checklist

---

# 41. What NOT to do

Do not:

1. Rewrite the entire repository from scratch.
2. Replace working architecture merely because another framework is fashionable.
3. Scatter provider-specific code through the application.
4. Put customer API keys in frontend code.
5. Store plaintext API keys.
6. Trust frontend tenant IDs.
7. Use local disk as permanent SaaS storage.
8. Make Baileys sessions part of API process lifecycle.
9. Hard-code plan names throughout the code.
10. Implement billing by simply incrementing one database balance field.
11. Make `/v1` API depend on UI implementation details.
12. Rename every Voysse identifier blindly.
13. Remove upstream compatibility code before replacement paths are tested.
14. Add features without corresponding authorization and quota tests.
15. Declare production readiness from a successful frontend build alone.

---

# 42. Future technology evaluation policy

New technologies should be introduced only when they solve a demonstrated problem.

Potential future additions to evaluate, not automatically adopt:

```text
PostgreSQL read replicas
Redis Cluster
S3/R2
OpenTelemetry
Prometheus/Grafana
Sentry or equivalent error tracking
Vault/KMS/secrets manager
container orchestration
Kubernetes
managed queues
event streaming
vector database / pgvector
```

The default preference is the simplest architecture that meets measured production requirements.

---

# 43. Relationship with InnoTech SaaS Core

Where the existing InnoTech SaaS Core provides reusable capabilities, this product should consume them rather than duplicate them.

Particularly relevant areas:

```text
multi-tenancy
security
AI gateway
provider routing
credit accounting
metering
prompt/versioning
agent runtime
safe tools
```

Integration must be modular so the Agent Factory can still run independently where necessary.

Do not create a hard circular dependency between repositories.

---

# 44. Commercial architecture

The platform supports three revenue paths:

```text
Direct SaaS
    Free -> Paid

Agency SaaS
    Agency -> Client subscriptions

White-label infrastructure
    Partner -> Partner customers
```

Platform revenue and AI infrastructure cost must be attributable at tenant/agent/model level.

This is why usage normalization and cost attribution are core architecture, not merely analytics.

---

# 45. Production readiness definition

The system is NOT production-ready merely because:

- signup works
- chat works
- WhatsApp works
- Docker starts
- frontend builds

Production readiness requires:

```text
security
+ tenant isolation
+ authorization
+ API stability
+ usage metering
+ quota enforcement
+ billing correctness
+ secret management
+ backups
+ recovery
+ observability
+ scaling
+ migration safety
+ automated tests
+ abuse controls
```

All must be verified.

---

# 46. Definition of Done for every future phase

A phase is complete only when:

1. Code is implemented.
2. Existing functionality remains intact unless intentionally changed.
3. Database migrations are created and tested.
4. Unit/integration tests are added.
5. Security implications are reviewed.
6. API contracts are documented.
7. UI behavior is verified where applicable.
8. Docker/deployment behavior is verified.
9. Failure cases are tested.
10. A rollback/migration strategy exists.
11. Git diff is reviewed for accidental vendor branding or secrets.
12. The phase is recorded in project documentation.

---

# 47. Future-reference checklist

Before starting any new feature, ask:

```text
Does this belong to Platform, Tenant, Agent Runtime, Provider, Channel,
Billing, Usage, or UI?

Is it tenant-scoped?

Does it require a permission?

Does it consume quota/credits?

Does it expose a secret?

Does it need an API contract?

Can it work with multiple providers?

Will it work with multiple API replicas?

Does it require durable object storage?

Does it require an async job?

How will it behave for FREE vs paid vs enterprise?

How will a white-label reseller use it?

How will we test cross-tenant access?
```

If these questions are not answered, the feature is not architecturally complete.

---

# 48. Immediate next implementation instruction

Do NOT begin by changing all branding strings.

The next engineering action should be a **Phase 0 production audit** that produces a file-by-file transformation map and identifies:

```text
KEEP
MODIFY
REFACTOR
NEW
DEPRECATE
MIGRATE
```

for:

```text
apps/api
apps/web
apps/whatsapp
migrations
Docker
environment files
tests
docs
brand assets
```

Then implement Phase 1 in small verified increments.

---

# 49. Architectural north star

The final platform should behave conceptually as:

```text
                         INNOTECH PLATFORM
                                |
                 +--------------+--------------+
                 |                             |
           SaaS Control Plane             AI Gateway
                 |                             |
       +---------+---------+          +--------+--------+
       |         |         |          |        |        |
    Tenants   Billing   Usage      OpenAI  Gemini  Anthropic
       |                              \       |       /
       |                               \      |      /
       +------ Agent Runtime -----------+-----+-----+
                     |
          +----------+----------+
          |          |          |
         Web      WhatsApp      API
          |          |          |
          +----------+----------+
                     |
                 End Users
```

**The core strategic decision:** InnoTech should own the tenant, agent, runtime, usage, billing and API layers while keeping AI providers and communication channels replaceable adapters.

That is the architecture that allows the same codebase to serve free users, paid SaaS customers, agencies, resellers and enterprise white-label deployments without creating separate products.

---

## Document control

This file is the production strategy baseline. Future architecture changes should update this document when they materially change tenancy, provider abstraction, public API, billing, white-label, security or deployment architecture.

Do not treat temporary implementation shortcuts as the target architecture.
