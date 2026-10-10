"""Standard exception hierarchy for the AI Gateway."""

from fastapi import HTTPException


class GatewayError(HTTPException):
    """Base exception for all Gateway errors. Maps cleanly to HTTP status codes."""

    def __init__(self, status_code: int = 502, detail: str = "AI Gateway error"):
        super().__init__(status_code=status_code, detail=detail)


class ProviderNotFoundError(GatewayError):
    def __init__(self, provider_id: str):
        super().__init__(status_code=400, detail=f"Provider '{provider_id}' is not registered or supported.")


class ProviderDisabledError(GatewayError):
    def __init__(self, provider_id: str):
        super().__init__(status_code=400, detail=f"Provider '{provider_id}' is disabled.")


class ModelNotFoundError(GatewayError):
    def __init__(self, model_id: str):
        super().__init__(status_code=404, detail=f"Model '{model_id}' is not registered in the model catalog.")


class ModelInactiveError(GatewayError):
    def __init__(self, model_id: str):
        super().__init__(status_code=400, detail=f"Model '{model_id}' is inactive or unverified and cannot be executed.")


class ModelCapabilityMismatchError(GatewayError):
    def __init__(self, model_id: str, capability: str):
        super().__init__(status_code=400, detail=f"Model '{model_id}' does not support required capability: {capability}.")


class ProviderModelMismatchError(GatewayError):
    def __init__(self, requested_provider: str, model_id: str, actual_provider: str):
        super().__init__(
            status_code=400,
            detail=f"Provider mismatch: requested provider '{requested_provider}' cannot serve model '{model_id}' (bound to provider '{actual_provider}').",
        )


class InvalidBaseUrlError(GatewayError):
    def __init__(self, reason: str = "Untrusted or invalid base URL"):
        super().__init__(status_code=400, detail=f"Invalid base URL: {reason}")


class CredentialResolutionError(GatewayError):
    def __init__(self, provider_id: str, reason: str = "No valid credential found"):
        super().__init__(status_code=400, detail=f"Credential resolution failed for provider '{provider_id}': {reason}")


class TenantSecurityError(GatewayError):
    def __init__(self, detail: str = "Tenant security boundary violated"):
        super().__init__(status_code=403, detail=detail)


class ProviderExecutionError(GatewayError):
    def __init__(self, provider_id: str, detail: str = "Provider execution failed"):
        super().__init__(status_code=502, detail=f"Provider '{provider_id}' error: {detail}")


class RoutingError(GatewayError):
    def __init__(self, detail: str = "No route found for request"):
        super().__init__(status_code=400, detail=detail)
