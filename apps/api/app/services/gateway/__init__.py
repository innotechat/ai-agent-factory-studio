"""Canonical export package for the AI Gateway."""

from .base_adapter import BaseProviderAdapter
from .credential_resolver import CredentialResolver
from .exceptions import (
    CredentialResolutionError,
    GatewayError,
    InvalidBaseUrlError,
    ModelCapabilityMismatchError,
    ModelInactiveError,
    ModelNotFoundError,
    ProviderDisabledError,
    ProviderExecutionError,
    ProviderModelMismatchError,
    ProviderNotFoundError,
    RoutingError,
    TenantSecurityError,
)
from .gateway import AIGateway
from .model_registry import ModelRegistry, get_model_registry
from .provider_registry import ProviderRegistry, get_provider_registry
from .routing import RouteDecision, RoutingPolicy
from .types import (
    FinishReason,
    GatewayMessage,
    GatewayResponse,
    GatewayUsage,
    ModelCapability,
    NormalizedToolCall,
    RegisteredModel,
    ResolvedCredential,
    ToolDefinition,
)

__all__ = [
    "AIGateway",
    "BaseProviderAdapter",
    "CredentialResolutionError",
    "CredentialResolver",
    "FinishReason",
    "GatewayError",
    "GatewayMessage",
    "GatewayResponse",
    "GatewayUsage",
    "InvalidBaseUrlError",
    "ModelCapability",
    "ModelCapabilityMismatchError",
    "ModelInactiveError",
    "ModelNotFoundError",
    "ModelRegistry",
    "NormalizedToolCall",
    "ProviderDisabledError",
    "ProviderExecutionError",
    "ProviderModelMismatchError",
    "ProviderNotFoundError",
    "ProviderRegistry",
    "RegisteredModel",
    "ResolvedCredential",
    "RouteDecision",
    "RoutingError",
    "RoutingPolicy",
    "TenantSecurityError",
    "ToolDefinition",
    "get_model_registry",
    "get_provider_registry",
]
