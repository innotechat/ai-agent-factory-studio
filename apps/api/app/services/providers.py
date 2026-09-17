import os
from sqlalchemy.orm import Session
from..models import ProviderCredential
from..security import decrypt_secret

OPENROUTER_BASE = os.getenv("OPENAI_API_BASE_URL", "https://openrouter.ai/api/v1")

PROVIDERS = {
    "openai": {"label": "OpenAI", "base_url": "https://api.openai.com/v1"},
    "anthropic": {"label": "Anthropic", "base_url": "https://api.anthropic.com/v1"},
}
SUPPORTED = set(PROVIDERS.keys())

def base_url_for(provider: str) -> str:
    # If env is set to openrouter, use it for openai provider
    if provider == "openai" and "openrouter.ai" in OPENROUTER_BASE:
        return OPENROUTER_BASE
    return PROVIDERS[provider]["base_url"]

def _is_openrouter_key(api_key: str) -> bool:
    return bool(api_key and api_key.startswith("sk-or-v1-"))

def resolve_provider_credentials(db: Session, agency_id, provider: str) -> tuple[str, str] | None:
    """(base_url, api_key) for an agency's provider key, or None if unknown or unset."""
    credential = db.query(ProviderCredential).filter(
        ProviderCredential.agency_id == agency_id,
        ProviderCredential.provider == provider
    ).first()
    if not credential or not credential.encrypted_api_key:
        return None
    api_key = decrypt_secret(credential.encrypted_api_key)
    base_url = base_url_for(provider)
    if _is_openrouter_key(api_key):
        base_url = "https://openrouter.ai/api/v1"
    return base_url, api_key

def resolve_agent_credentials(db: Session, agent):
    """(base_url, api_key) for the agent's provider using the agency's stored key."""
    return resolve_provider_credentials(db, agent.agency_id, agent.provider)
