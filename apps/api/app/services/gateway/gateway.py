"""AI Gateway - Unified entry point for all model executions.

Request flow:
Application / Agent
       ↓
    AIGateway
       ↓
   RoutingPolicy
       ↓
 CredentialResolver
       ↓
 ProviderAdapter (OpenAI / Anthropic / Google / Mock)
       ↓
 Normalized Response + Normalized Usage
"""

import logging
import uuid
from typing import Any
from sqlalchemy.orm import Session

from...models import User
from .credential_resolver import CredentialResolver
from .exceptions import GatewayError, ProviderExecutionError
from .model_registry import ModelRegistry, get_model_registry
from .provider_registry import ProviderRegistry, get_provider_registry
from .routing import RoutingPolicy
from .types import (
    GatewayMessage,
    GatewayResponse,
    ToolDefinition,
)

logger = logging.getLogger(__name__)


class AIGateway:
    """Production provider-neutral AI Gateway."""

    def __init__(
        self,
        db: Session,
        provider_registry: ProviderRegistry | None = None,
        model_registry: ModelRegistry | None = None,
        routing_policy: RoutingPolicy | None = None,
    ):
        self.db = db
        self.provider_registry = provider_registry or get_provider_registry()
        self.model_registry = model_registry or get_model_registry()
        self.routing_policy = routing_policy or RoutingPolicy(self.model_registry)
        self.credential_resolver = CredentialResolver(db)

    async def complete(
        self,
        agency_id: uuid.UUID | str,
        model: str,
        messages: list[GatewayMessage],
        *,
        user: User | None = None,
        provider: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolDefinition] | None = None,
        allow_fallback: bool = True,
        **kwargs: Any,
    ) -> GatewayResponse:
        """Route request through policy, resolve credentials, and execute adapter."""
        requires_tools = bool(tools)
        decision = self.routing_policy.resolve_route(
            requested_model=model,
            requested_provider=provider,
            requires_tools=requires_tools,
            allow_fallback=allow_fallback,
        )

        # 1. Attempt primary provider and model
        try:
            return await self._execute_provider(
                agency_id=agency_id,
                user=user,
                provider_id=decision.primary_provider,
                model_id=decision.primary_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                **kwargs,
            )
        except ProviderExecutionError as primary_exc:
            # 2. Policy-controlled fallback (ONLY if primary failed due to genuine provider execution failure)
            if allow_fallback and decision.fallback_provider and decision.fallback_model:
                logger.warning(
                    "Primary provider/model %s/%s failed with provider execution error (%s). Executing policy fallback to %s/%s",
                    decision.primary_provider,
                    decision.primary_model,
                    primary_exc.detail,
                    decision.fallback_provider,
                    decision.fallback_model,
                )
                try:
                    return await self._execute_provider(
                        agency_id=agency_id,
                        user=user,
                        provider_id=decision.fallback_provider,
                        model_id=decision.fallback_model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        tools=tools,
                        **kwargs,
                    )
                except Exception as fallback_exc:
                    logger.error("Fallback provider execution also failed: %s", str(fallback_exc))
                    # Re-raise primary exception to preserve error context
                    raise primary_exc from fallback_exc

            # No fallback or fallback disabled
            raise primary_exc

    async def _execute_provider(
        self,
        agency_id: uuid.UUID | str,
        user: User | None,
        provider_id: str,
        model_id: str,
        messages: list[GatewayMessage],
        temperature: float | None,
        max_tokens: int | None,
        tools: list[ToolDefinition] | None,
        **kwargs: Any,
    ) -> GatewayResponse:
        """Resolve credentials and invoke adapter safely."""
        adapter = self.provider_registry.require_adapter(provider_id)
        credential = self.credential_resolver.resolve(
            provider_id=provider_id,
            agency_id=agency_id,
            user=user,
        )

        return await adapter.chat(
            credential=credential,
            model=model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs,
        )
