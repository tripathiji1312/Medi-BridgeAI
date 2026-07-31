from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Mirrors packages/shared-types HealthResponse. Kept in parity by hand
    until a schema generator is introduced (flagged, not added, in Phase 0)."""

    model_config = {"strict": True}

    status: str
    service: str
    version: str
