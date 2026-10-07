from typing import Any
import uuid

from sqlalchemy.orm import Session

from ..models import UsageRecord
from .ai import Completion


def record_usage(db: Session, agency_id: uuid.UUID, agent_id: uuid.UUID | None, provider: str, model: str, completion: Any) -> None:
    """Store token usage for a completion or GatewayResponse. The caller owns the commit."""
    if hasattr(completion, "usage"):
        input_tokens = completion.usage.input_tokens
        output_tokens = completion.usage.output_tokens
    else:
        input_tokens = getattr(completion, "input_tokens", 0)
        output_tokens = getattr(completion, "output_tokens", 0)

    if input_tokens <= 0 and output_tokens <= 0:
        return
    db.add(
        UsageRecord(
            agency_id=agency_id,
            agent_id=agent_id,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
    )
