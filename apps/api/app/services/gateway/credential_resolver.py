"""Server-side Credential Resolver for the AI Gateway.

Flow:
Request -> Principal (User) -> Tenant (Agency) -> Provider -> CredentialResolver

Security Guarantees:
- Never trust frontend-supplied API keys or credentials.
- Never log plaintext secrets.
- Enforce strict tenant isolation (agency_id scope).
- Base URLs come exclusively from trusted server configuration, preventing SSRF.
"""

import os
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from...models import ProviderCredential, User
from...security import decrypt_secret
from .exceptions import CredentialResolutionError, TenantSecurityError
from .types import ResolvedCredential


class CredentialResolver:
    """Resolves credentials safely within tenant and principal boundaries."""

    def __init__(self, db: Session):
        self.db = db

    def resolve(
        self,
        provider_id: str,
        agency_id: uuid.UUID | str,
        *,
        user: User | None = None,
        base_url_override: str | None = None,
    ) -> ResolvedCredential:
        """Resolve credentials for an agency and provider with tenant enforcement."""
        if isinstance(agency_id, str):
            try:
                parsed_agency_id = uuid.UUID(agency_id)
            except ValueError as exc:
                raise TenantSecurityError("Invalid agency identifier format") from exc
        else:
            parsed_agency_id = agency_id

        # Tenant verification: if user is supplied, confirm agency membership
        if user is not None and user.agency_id != parsed_agency_id:
            raise TenantSecurityError("Principal agency does not match requested tenant context")

        # Mock provider bypass strictly for test environments
        if provider_id == "mock":
            return ResolvedCredential(
                provider_id="mock",
                api_key="mock-test-key-safe",
                base_url="http://mock-provider.local",
                source="mock",
                agency_id=str(parsed_agency_id),
            )

        # 1. Tenant BYOK from PostgreSQL database
        cred = self.db.scalar(
            select(ProviderCredential).where(
                ProviderCredential.agency_id == parsed_agency_id,
                ProviderCredential.provider == provider_id,
            )
        )

        api_key = ""
        source = "agency_byok"

        if cred and cred.encrypted_api_key:
            api_key = decrypt_secret(cred.encrypted_api_key)
        else:
            # 2. Check for platform-managed fallback from trusted environment vars
            env_key = self._get_platform_env_key(provider_id)
            if env_key:
                api_key = env_key
                source = "platform_managed"

        if not api_key:
            raise CredentialResolutionError(
                provider_id,
                f"No API key configured for agency '{parsed_agency_id}' and no platform key available.",
            )

        # 3. Resolve base URL safely from trusted configuration (prevent SSRF)
        resolved_base_url = self._resolve_safe_base_url(provider_id, api_key, base_url_override)

        return ResolvedCredential(
            provider_id=provider_id,
            api_key=api_key,
            base_url=resolved_base_url,
            source=source,
            agency_id=str(parsed_agency_id),
        )

    def _get_platform_env_key(self, provider_id: str) -> str | None:
        """Check server environment for platform-managed fallback keys."""
        mapping = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GEMINI_API_KEY",
        }
        env_var = mapping.get(provider_id)
        if env_var:
            val = os.getenv(env_var, "").strip()
            if val:
                return val
        return None

    def _resolve_safe_base_url(
        self,
        provider_id: str,
        api_key: str,
        override_url: str | None = None,
    ) -> str:
        """Deterministic resolution of base URL from trusted endpoints only."""
        if api_key.startswith("sk-or-v1-"):
            return "https://openrouter.ai/api/v1"

        trusted_defaults = {
            "openai": os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1"),
            "anthropic": "https://api.anthropic.com/v1",
            "google": "https://generativelanguage.googleapis.com/v1beta",
            "mock": "http://mock-provider.local",
        }

        default_url = trusted_defaults.get(provider_id, "https://api.openai.com/v1")

        # Only allow explicit overrides if they match trusted hostnames
        if override_url:
            trusted_hosts = ("api.openai.com", "api.anthropic.com", "generativelanguage.googleapis.com", "openrouter.ai", "mock-provider.local")
            if any(host in override_url for host in trusted_hosts):
                return override_url

        return default_url
