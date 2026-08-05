from __future__ import annotations

from pydantic import BaseModel

from app.ner.schemas import MedicalEntity


class EmergencyDetectionRequest(BaseModel):
    model_config = {"strict": True}

    text: str
    language: str = "hi"


class EmergencyDetectionResponse(BaseModel):
    """`alert` is never shown bare (Blueprint Section 1 Principle 2) --
    `reason` always names the matched phrase(s) so a clinician sees exactly
    why the banner fired, and `matches` carries the full span-grounded
    entities (Section 11.1) for inline highlighting if the UI wants it."""

    model_config = {"strict": True}

    alert: bool
    matches: list[MedicalEntity]
    reason: str | None
    lexicon_version: str
