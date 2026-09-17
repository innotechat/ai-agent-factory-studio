# Phase 0 — Repository Production Audit

**Repository:** `innotechat/ai-agent-factory`  
**Target:** InnoTech AI Agent Factory — multi-tenant, free/paid, API-first, white-label, reseller-capable SaaS  
**Audit type:** Architecture + codebase transformation audit  
**Status:** Baseline audit complete; implementation has not yet started  
**Audit basis:** Current `main` branch repository structure and representative backend, database, provider, usage, auth, frontend, dependency and migration files.

> This document is the implementation baseline. It records what the repository currently is, what must be preserved, what must change, and the order in which changes should be made. Do not use a broad search-and-replace or a full rewrite as a substitute for this audit.

---

## 1. Executive Finding

The repository is **not a throwaway prototype**. It already contains a substantial working agent-platform foundation: FastAPI + SQLAlchemy + Alembic, Next.js/React/Tailwind, PostgreSQL, agency/client/agent hierarchy, provider credentials, agent tools/MCP, knowledge, conversations/inbox, WhatsApp, client portal, domains, reusable solutions and usage recording.

The correct production path is therefore **incremental architectural extraction and hardening**, not a rewrite.

The central architectural limitation is that the current product is **agency-centric**, while the target product must be **platform/tenant-centric**. The current provider and usage layers are also too close to individual provider implementations for the planned OpenAI-compatible API, managed AI, BYOK, model routing, metering and reseller hierarchy.

### Primary transformation

```text
Current
Agency -> Users/Clients -> Agents -> Provider

Target
InnoTech Platform
    -> Tenant / Organization
        -> Memberships / RBAC
        -> Clients / Workspaces
        -> Agents
        -> Knowledge / Tools / Channels
        -> API Keys
        -> Usage / Credits / Billing
        -> Branding / Domains
        -> Reseller ancestry when applicable
    -> AI Gateway
        -> Model Registry
        -> Provider Adapters
        -> Routing / Resilience / Cost
```

### Overall audit disposition

| Area | Current state | Decision | Priority |
|---|---|---|---|
| FastAPI API | Working foundation | **KEEP / REFACTOR** | P0 |
| SQLAlchemy + PostgreSQL | Strong foundation | **KEEP / REFACTOR** | P0 |
| Alembic migrations | Mature migration history | **KEEP / HARDEN** | P0 |
| Next.js web app | Working product UI | **KEEP / REFACTOR** | P1 |
| Agency tenancy | Functional | **MIGRATE toward canonical Tenant** | P0 |
| Auth/dependencies | Admin-centric in places | **REFACTOR** | P0 |
| Provider layer | OpenAI/Anthropic-centric | **REFACTOR into AI Gateway** | P0 |
| Usage | Token recording exists | **REFACTOR into event + ledger architecture** | P0 |
| Billing/plans | Not yet the target architecture | **NEW** | P1 |
| API keys/OpenAI compatibility | Not sufficient for target | **NEW** | P0 |
| White-label | Partial portal/domain capability | **REFACTOR / EXTEND** | P1 |
| Reseller hierarchy | Not target-complete | **NEW** | P2 |
| WhatsApp | Existing implementation | **KEEP / ISOLATE runtime** | P1 |
| MCP/custom HTTP tools | Valuable existing feature | **KEEP / SECURITY HARDEN** | P0 |
| Object storage | Needs platform abstraction | **NEW / MIGRATE** | P1 |
| Async workers/queues | Needs production architecture | **NEW / EXTRACT** | P1 |
| Observability | Needs unified platform layer | **NEW / HARDEN** | P1 |
| Voysse rebrand | Legacy identity remains | **MIGRATE carefully** | P1 |
| Legal/license compatibility | Must be verified before commercial hosting | **BLOCKER TO COMMERCIALIZATION REVIEW** | P0 |

---

# 2. What Must Be Preserved

Do not delete or rewrite these capabilities merely to make the code look cleaner:

- FastAPI application and existing router structure.
- SQLAlchemy models and existing tenant/ownership constraints.
- Alembic migration history.
- Agency/client/agent relationship semantics while compatibility migration is underway.
- Provider credential encryption/storage mechanism.
- Existing agent configuration fields: instructions, personality, business context, model/generation configuration, memory and widget settings.
- Knowledge/document and QA functionality.
- HTTP tools and MCP tools.
- Existing conversation/inbox functionality.
- Web widget/channel foundations.
- WhatsApp support and its existing webhook/session concepts.
- Client portal and portal branding/domain capabilities.
- Reusable solution/version/install architecture.
- Existing security controls such as session versioning, rate limiting, tenant filters and SSRF-related checks.
- Existing tests and CI/build configuration.

The production transformation must improve these capabilities rather than accidentally removing them.

---

# 3. P0 Architecture Findings

## 3.1 Agency is currently the effective tenant boundary

The current data model and services repeatedly use `agency_id` as the ownership boundary. This works for the existing agency product but is too narrow for:

- direct Free users;
- direct paid customers;
- enterprise organizations;
- resellers;
- white-label tenants;
- future tenant-to-tenant ancestry.

### Required action

Introduce a canonical tenant abstraction without immediately deleting `Agency`.

Recommended migration sequence:

1. Add `tenants`.
2. Add tenant type and lifecycle state.
3. Add compatibility mapping `agency.tenant_id`.
4. Add `tenant_id` to new platform-level tables.
5. Introduce request-scoped `tenant_context`.
6. Migrate new code to tenant scope.
7. Backfill existing agencies into tenants.
8. Migrate existing domain objects incrementally.
9. Keep `Agency` as a compatibility facade until the migration is proven.
10. Only later consider a destructive rename.

**Do not globally rename `agency_id` to `tenant_id` in one commit.** Existing foreign keys, migrations, queries and APIs need controlled migration.

---

## 3.2 Authentication/dependency layer is too admin-centric

The current dependency design contains separate inbox/current-user behavior and a `get_current_user` path that assumes an admin role. That is incompatible with a SaaS product where a user may be:

- platform administrator;
- tenant owner;
- tenant admin;
- manager;
- operator;
- developer;
- client admin/operator;
- viewer;
- reseller owner.

### Required action

Create a centralized authorization layer:

```text
get_current_principal()
get_current_tenant()
require_role(...)
require_permission(...)
require_scope(...)
require_feature(...)
require_quota(...)
```

The route should not decide authorization from arbitrary request-body tenant IDs. The authenticated principal and server-side membership/ancestry must establish scope.

---

## 3.3 Provider implementation is too coupled

The current provider service has explicit provider dictionaries and special-case behavior for OpenAI/OpenRouter-style endpoints. This is a useful starting implementation, but it will not scale cleanly to:

- OpenAI;
- Anthropic;
- Gemini;
- OpenRouter;
- Azure OpenAI;
- custom OpenAI-compatible providers;
- InnoTech-managed models;
- BYOK credentials;
- routing policies;
- circuit breakers;
- cost-aware routing.

### Required target

```text
ProviderRegistry
ModelRegistry
ProviderAdapter
CredentialResolver
RoutingPolicy
CircuitBreaker
UsageNormalizer
CostCalculator
```

Provider-specific logic must stay inside adapters. Business logic should consume normalized request/response/usage contracts.

---

## 3.4 Usage is currently recording, not yet billing-grade metering

The existing usage service records agency, agent, provider, model and token counts. This is useful, but insufficient for the final commercial system.

The target requires:

```text
usage_events
usage_hourly
usage_daily
usage_monthly
credit_accounts
credit_ledger
credit_reservations
credit_settlements
```

Every billable AI request must be attributable to tenant, user, agent, provider, model and operation, with a stable request/correlation ID.

The existing usage recorder should be retained as a compatibility layer while the new metering pipeline is introduced.

---

# 4. Detailed File / Module Transformation Map

The following map is the implementation reference. Status values are intentional:

- **KEEP** — preserve as-is except normal maintenance.
- **MODIFY** — targeted changes; ownership remains in current module.
- **REFACTOR** — extract architecture without losing behavior.
- **NEW** — introduce a new bounded module.
- **DEPRECATE** — retain temporarily for compatibility; stop adding new dependencies.
- **MIGRATE** — data/API transition required.

## 4.1 API application

| Path / area | Action | Production work |
|---|---|---|
| `apps/api/app/main.py` | MODIFY | central app lifecycle, middleware, request IDs, observability, versioned API routing |
| `apps/api/app/config.py` | REFACTOR | typed production config, fail-fast secrets, platform/provider/storage/queue/billing separation |
| `apps/api/app/deps.py` | REFACTOR | principal/tenant/permission/quota dependencies |
| `apps/api/app/security.py` | HARDEN | sessions, API keys, CSRF/cookie rules, secret handling, auth error model |
| `apps/api/app/models.py` | REFACTOR | introduce canonical tenant/RBAC/billing/usage/API-key models incrementally |
| `apps/api/app/database.py` | KEEP / HARDEN | connection pooling, health checks, transaction boundaries |
| `apps/api/app/routers/*` | MODIFY | enforce tenant scope and permissions consistently |
| provider routers/services | REFACTOR | move provider selection into AI Gateway |
| usage service | REFACTOR | event metering + credits + cost attribution |
| agent service/runtime | REFACTOR | consume AI Gateway instead of direct provider logic |
| tool services | HARDEN | SSRF, timeout, redirect, response-size and allowlist controls |
| WhatsApp modules | ISOLATE | keep stateful session processing outside API request lifecycle where possible |

---

## 4.2 Database

### Existing strength

The migration history already contains deliberate tenant-isolation constraints. The reusable-solutions migration, for example, adds composite ownership constraints and scoped foreign keys between solutions, clients and agents. This pattern should be extended rather than discarded.

### Required new model groups

```text
Tenancy
- tenants
- tenant_memberships
- tenant_settings
- tenant_hierarchy / parent_tenant_id where required

Identity
- users
- memberships
- roles
- permissions
- role_permissions
- sessions
- api_keys

AI
- providers
- provider_credentials
- models
- model_access
- routing_policies
- provider_health

Commercial
- plans
- plan_features
- subscriptions
- subscription_items
- invoices
- payments
- payment_events

Usage
- usage_events
- usage_hourly
- usage_daily
- usage_monthly
- credit_accounts
- credit_ledger
- credit_reservations
- credit_settlements

White label
- brand_settings
- domains
- domain_verifications

Platform
- feature_flags
- audit_logs
- webhook_deliveries
- idempotency_keys
```

### Database rule

Every new tenant-owned record must have an explicit ownership path that can be verified by database constraints and server-side authorization. Avoid relying only on frontend filtering.

---

# 5. API Transformation

## 5.1 Current API model

The current API is product-oriented around agency/client/agent functionality.

## 5.2 Target API model

Create a stable `/v1` namespace independent of the internal UI architecture.

Initial compatibility surface:

```text
GET  /v1/models
POST /v1/chat/completions
POST /v1/responses
POST /v1/embeddings
POST /v1/audio/transcriptions
```

Native platform surface:

```text
/v1/agents
/v1/agents/{agent_id}
/v1/agents/{agent_id}/responses
/v1/agents/{agent_id}/knowledge
/v1/agents/{agent_id}/tools
/v1/usage
/v1/api-keys
/v1/webhooks
```

The OpenAI-compatible layer must translate into the internal normalized AI Gateway request model. It must not become a second provider implementation.

---

# 6. API Key Architecture

## Required new implementation

API keys must be stored as hashes, not plaintext secrets.

Minimum record:

```text
id
 tenant_id
 name
 prefix
 secret_hash
 scopes
 last_used_at
 expires_at
 revoked_at
 created_by
 created_at
```

The full secret should be shown only once at creation. Requests authenticate using the hash/prefix lookup mechanism.

Required capabilities:

- scoped permissions;
- expiration;
- revocation;
- rotation;
- usage tracking;
- audit trail;
- optional IP restrictions for enterprise;
- rate limits;
- idempotency support for mutations.

---

# 7. Free / Paid Architecture

Do not write code such as:

```python
if plan == "pro":
    ...
```

throughout the application.

Use entitlements:

```text
agents.max
team_members.max
messages.monthly
api.enabled
api.requests.monthly
whatsapp.enabled
custom_domain.enabled
white_label.enabled
mcp.enabled
advanced_models.enabled
storage.gb
```

The plan defines the entitlements. The enforcement service evaluates entitlements against current usage.

Initial plan names may be:

```text
FREE
STARTER
PRO
BUSINESS
AGENCY
ENTERPRISE
```

Pricing and exact limits must be derived from actual provider cost, storage, messaging, support and infrastructure economics. Do not hardcode arbitrary limits before the cost model is defined.

---

# 8. AI Gateway Transformation

This is the most important technical refactor after tenancy.

## Target request flow

```text
API / Agent Runtime
      |
      v
AI Gateway
      |
      +--> credential resolver
      +--> entitlement/quota check
      +--> model registry
      +--> routing policy
      +--> provider health
      +--> circuit breaker
      +--> provider adapter
      +--> normalized response
      +--> usage/cost event
      +--> credit settlement
```

## Provider adapters

Initial adapters:

```text
OpenAIAdapter
AnthropicAdapter
GeminiAdapter
OpenRouterAdapter
OpenAICompatibleAdapter
AzureOpenAIAdapter (when required)
```

Do not add all adapters in one speculative rewrite. Build the interface first and migrate the currently used providers behind it.

---

# 9. Managed AI + BYOK

The product must support both:

### InnoTech-managed

User pays InnoTech. InnoTech owns provider credentials and routing/cost policy.

### BYOK

Tenant supplies its own provider credential. Credential remains server-side and is never returned to the browser.

Credential resolution order should be explicit and auditable, for example:

```text
agent override (if enabled)
-> tenant BYOK
-> reseller credential policy
-> platform managed credential
```

The final order must be represented by a policy, not scattered `if` statements.

---

# 10. White-Label Transformation

The existing client portal/domain capabilities are valuable and should become the foundation for the broader white-label system.

## New model

`BrandSettings` should support:

- brand name;
- legal name;
- logo/light/dark variants;
- favicon;
- colors;
- typography;
- login background;
- email branding;
- support contact;
- legal links;
- powered-by policy;
- custom CSS only under controlled validation.

Domains should be modeled independently from client records so one domain can represent the platform, tenant portal, API and widget identities as needed.

White-label levels should be incremental:

```text
branding
-> custom domain
-> custom login/portal
-> widget branding
-> email branding
-> API identity
-> platform-brand hiding
-> reseller hierarchy
```

---

# 11. Reseller Architecture

Do not make reseller support a collection of special UI cases.

Use tenant ancestry:

```text
InnoTech Platform
    |
    +-- Reseller Tenant
          |
          +-- Customer Tenant A
          +-- Customer Tenant B
```

Every reseller-visible resource must be authorized by ancestry, not by a client-supplied ID.

Reseller capabilities:

- create/manage customers;
- assign plans/entitlements;
- manage branding;
- manage domains;
- provision agents/templates;
- view permitted usage/revenue;
- manage reseller team;
- optionally use reseller API keys.

---

# 12. Channels and Runtime

The current agent/channel functionality should converge on one Agent Runtime.

```text
Channel Adapter
    -> inbound event
    -> tenant resolution
    -> agent resolution
    -> identity/session
    -> memory
    -> knowledge
    -> tools/MCP
    -> AI Gateway
    -> response
    -> channel adapter
    -> usage/credits/events
```

Web, WhatsApp, future Instagram/Facebook and API channels should not each implement their own AI business logic.

### WhatsApp

Baileys is stateful. It must not become a hidden dependency of every API process. Move session processing toward a dedicated worker/service boundary as scale increases.

---

# 13. Storage and Background Work

## Object storage

Move durable uploaded content toward S3-compatible storage:

- S3;
- Cloudflare R2;
- MinIO for local development.

Database stores metadata/object keys, not large binary payloads.

## Worker layer

Introduce a queue abstraction for:

- document parsing;
- embeddings;
- AI background jobs;
- audio/image processing;
- webhooks;
- WhatsApp jobs;
- email;
- usage aggregation;
- billing events;
- domain verification;
- analytics.

Redis-backed queues are sufficient as an initial implementation if the queue interface remains abstract.

---

# 14. Security Audit Priorities

Before exposing a public paid API, verify:

### Authentication
- secure cookie/session settings;
- session revocation/versioning;
- API key hashing;
- key rotation/revocation;
- brute-force controls.

### Tenant isolation
- every read path has tenant scope;
- every write path has tenant scope;
- cross-tenant object IDs cannot be used for authorization bypass;
- composite foreign keys are used where valuable;
- reseller ancestry is enforced server-side.

### Tools / SSRF
- block private/loopback/link-local targets;
- DNS rebinding protection;
- redirect policy;
- protocol allowlist;
- method allowlist;
- connect/read timeout;
- response-size limit;
- enterprise allowlist where needed.

### Webhooks
- signature verification;
- timestamp/replay protection where supported;
- idempotency;
- bounded retries;
- dead-letter handling.

### Files
- MIME/extension validation;
- size limits;
- object isolation;
- malware scanning before high-risk processing;
- signed temporary URLs where applicable.

### Secrets
- no frontend exposure;
- no plaintext database/API credential storage;
- production secret manager/KMS path when scale requires it;
- secrets excluded from logs.

---

# 15. Observability

Introduce a request context containing:

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

Measure:

- request latency;
- provider latency;
- queue latency;
- status/error rate;
- token usage;
- estimated provider cost;
- billed units;
- retries;
- circuit-breaker events;
- quota denials;
- credit reservation failures.

Use OpenTelemetry-compatible tracing so the platform can later connect to the chosen observability stack without rewriting application instrumentation.

---

# 16. Frontend Transformation

The existing Next.js application should remain the main product UI.

Refactor toward role-aware surfaces:

### Platform Admin

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
Providers
Models
Domains
Channels
Jobs
Health
Feature Flags
Audit
Security/Abuse
```

### Customer

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

### Reseller

```text
Dashboard
Customers
Agents/Templates
Usage
Revenue/Billing
Team
Branding
Domains
API
Settings
```

The frontend must not become the enforcement layer. It displays server-authorized capabilities; the API remains authoritative.

---

# 17. Branding Migration

The repository is derived from Voysse and contains legacy product identity.

Do **not** blindly replace every occurrence of `Voysse`, `voysse`, `openvoiss`, etc.

Perform a classified inventory:

```text
A. User-visible branding -> replace
B. Internal identifiers -> migrate only with compatibility plan
C. URLs/domains -> replace after deployment mapping exists
D. Environment variable names -> migrate with fallback period
E. Database identifiers -> migration required
F. Documentation/examples -> update
G. Third-party/legal/license references -> verify before modifying
H. Historical migration identifiers -> normally preserve
```

Brand configuration should become centralized so future white-label branding does not require source edits.

---

# 18. Legal / Commercial Blocker

The source repository's upstream license and any FSL/open-source restrictions must be reviewed against the intended commercial hosted/white-label business model before launch.

This audit does **not** make a legal determination. It identifies the review as a release blocker because the product strategy includes hosted commercial SaaS and white-label/reseller operation.

Required before commercialization:

- verify current license text and version;
- identify upstream attribution requirements;
- identify restrictions on hosted/competing service use;
- document all modified/forked components;
- obtain legal review where necessary.

---

# 19. Testing Required Before Each Migration Stage

Every architectural change must add or preserve tests for:

### Unit
- provider normalization;
- routing;
- entitlement evaluation;
- credit reservation/settlement;
- permission checks.

### Integration
- tenant creation;
- tenant isolation;
- membership/RBAC;
- provider credentials;
- API key authentication;
- billing webhooks;
- usage event creation.

### Security
- cross-tenant IDOR attempts;
- expired/revoked API keys;
- SSRF attempts;
- webhook replay;
- unauthorized reseller ancestry access;
- secret leakage.

### API contract
- `/v1/models`;
- `/v1/chat/completions`;
- `/v1/responses`;
- normalized errors;
- idempotency.

### E2E
- signup -> Free tenant -> agent -> chat;
- upgrade -> paid entitlement;
- BYOK provider -> agent response;
- API key -> OpenAI-compatible request;
- white-label domain -> branded portal;
- reseller -> customer provisioning.

---

# 20. Exact Implementation Order

This is the approved order unless a later audit discovers a dependency that makes a step unsafe.

## Phase 0A — Baseline freeze

- record current branch/commit;
- run existing backend tests;
- run frontend typecheck/lint/build;
- run migration validation;
- record environment requirements;
- record current API routes;
- record current DB tables;
- record current Voysse identifiers;
- record current provider behavior.

**No product refactor in this step.**

## Phase 0B — Architecture scaffolding

Create the following bounded modules without changing behavior yet:

```text
app/core/request_context.py
app/core/permissions.py
app/core/entitlements.py
app/core/errors.py
app/core/idempotency.py
app/tenancy/
app/identity/
app/ai_gateway/
app/usage/
app/billing/
app/white_label/
app/platform/
```

Only introduce interfaces first.

## Phase 1 — Canonical tenant/RBAC

- Tenant model;
- membership model;
- roles/permissions;
- tenant context;
- route authorization;
- agency compatibility mapping.

## Phase 2 — AI Gateway

- normalized request/response contracts;
- provider adapters;
- model registry;
- credential resolver;
- routing policy;
- circuit breaker;
- normalized usage.

## Phase 3 — Public `/v1` API + API keys

- API key model/service;
- OpenAI-compatible endpoints;
- native agent API;
- stable errors;
- rate limits;
- idempotency.

## Phase 4 — Usage + credits

- usage events;
- cost calculation;
- atomic reservation;
- settlement/release;
- tenant dashboards.

**Reuse compatible components from `@innotech/saas-core` rather than duplicating credit accounting.**

## Phase 5 — Plans + billing

- plan/feature catalog;
- entitlements;
- subscription state machine;
- payment provider abstraction;
- webhook processing;
- invoices/payments;
- Free plan provisioning.

## Phase 6 — White-label

- brand settings;
- custom domains;
- domain verification;
- portal/widget/email/API branding.

## Phase 7 — Reseller

- tenant ancestry;
- reseller permissions;
- provisioning;
- reseller billing/usage visibility;
- reseller branding.

## Phase 8 — Scale

- workers/queue;
- object storage;
- WhatsApp session isolation;
- distributed cache/rate limiting;
- observability;
- load testing.

## Phase 9 — Production certification

- security tests;
- tenant-isolation tests;
- API compatibility tests;
- migration rehearsal;
- backup/restore test;
- failure injection;
- load test;
- deployment rollback test;
- commercial/legal review.

Only after this should the product be described internally as production-ready.

---

# 21. What We Must NOT Do

1. Do not rewrite the entire repository.
2. Do not replace FastAPI/Next.js simply for modernization.
3. Do not move every table to a new database in one migration.
4. Do not make frontend code authoritative for plan/permission enforcement.
5. Do not expose provider keys to browsers.
6. Do not keep plaintext provider/API credentials.
7. Do not put provider-specific business logic throughout agents/channels/routes.
8. Do not make plan names the enforcement mechanism.
9. Do not use a mutable balance as the sole billing record.
10. Do not run stateful Baileys sessions as hidden in-process API state at scale.
11. Do not store large durable files in PostgreSQL.
12. Do not add Kubernetes before the workload requires it.
13. Do not add a separate vector database before pgvector/Postgres or measured workload requirements justify it.
14. Do not rename historical migration identifiers casually.
15. Do not remove old agency APIs until compatibility migration is complete.
16. Do not perform blind global Voysse string replacement.
17. Do not claim production readiness because the frontend builds.
18. Do not call a feature complete until its auth, tenant isolation, quota/credit and failure tests exist.

---

# 22. Definition of Done for Every Future Feature

Before merging a feature, answer all of these:

```text
[ ] Which tenant owns it?
[ ] Which user/role can access it?
[ ] Which permission controls it?
[ ] Is there an entitlement/quota?
[ ] Does it consume credits or billable usage?
[ ] Does it contain a secret?
[ ] Is the secret encrypted/hashed and server-side only?
[ ] Does it need an API contract?
[ ] Does it need idempotency?
[ ] Does it need async processing?
[ ] Is durable data in PostgreSQL/object storage appropriately?
[ ] Is provider logic isolated behind the AI Gateway?
[ ] Does it work for Free and Paid tenants where intended?
[ ] Does it work for reseller/white-label tenants where intended?
[ ] Are cross-tenant access tests present?
[ ] Are failure/timeout/retry paths tested?
[ ] Is it observable with request/trace/tenant context?
[ ] Is migration/backward compatibility addressed?
```

A feature is not production-complete until the relevant answers are yes or an explicit architecture decision records why not.

---

# 23. Immediate Next Action — Phase 0A

The next coding task is **not rebranding**.

Run the baseline verification and produce a machine-checkable inventory of:

1. current API routes;
2. current database tables and foreign keys;
3. current Alembic head and migration chain;
4. current authentication/authorization paths;
5. all provider calls;
6. all usage recording paths;
7. all tenant/agency ownership queries;
8. all storage/file upload paths;
9. all background/async jobs;
10. all Voysse/OpenVoiss branding identifiers;
11. current tests and test gaps;
12. current deployment/environment assumptions.

Then create a **file-by-file implementation matrix** using:

```text
KEEP
MODIFY
REFACTOR
NEW
DEPRECATE
MIGRATE
```

No large code change should begin until that matrix is complete.

---

# 24. Future Reference — Architectural North Star

Whenever work resumes after a break, start from this model:

```text
                     INNOTECH PLATFORM
                            |
              +-------------+-------------+
              |                           |
       SaaS CONTROL PLANE             AI GATEWAY
              |                           |
       +------+-------+          +--------+---------+
       |      |       |          |        |         |
    Tenant  Billing Usage      Models   Routing  Providers
       |      |       |          |        |         |
       +------+-------+----------+--------+---------+
              |
         AGENT RUNTIME
              |
      +-------+--------+---------+----------+
      |       |        |         |          |
  Knowledge Tools    Memory   Channels    API
      |       |        |         |          |
      +-------+--------+---------+----------+
              |
        Free / Paid / Enterprise
              |
       White-label / Reseller
```

The repository should evolve toward this architecture **without destroying the working product underneath it**.

## Golden rule

> **Preserve working behavior, extract stable interfaces, migrate ownership and billing boundaries incrementally, and only then rename or remove legacy structures.**

This rule should govern every future implementation decision in `ai-agent-factory`.
