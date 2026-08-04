from __future__ import annotations

from pydantic import BaseModel, Field


class MiscommunicationResult(BaseModel):
    """Mirrors services/clinical-nlp/app/miscommunication/schemas.py
    MiscommunicationResult -- kept in parity by hand, same as every other
    cross-service schema in this build (see packages/shared-types for the
    TS-side equivalent pattern)."""

    model_config = {"strict": True}

    consistent: bool
    similarity_score: float = Field(ge=0.0, le=1.0)
    negation_flip_detected: bool
    reason: str
