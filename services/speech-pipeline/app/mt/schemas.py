from __future__ import annotations

from pydantic import BaseModel, Field


class TranslationSegment(BaseModel):
    """MT output attached to a finalized ASR TranscriptEvent. No independent
    confidence field yet -- Blueprint Section 8 Phase 2 scope is explicitly
    "confidence scoring v1 (ASR confidence only, MT self-consistency added
    next)"; back-translation-based MT confidence is Phase 4. Displaying a
    fabricated MT-quality number now would violate the "no numeric
    fabrication" rule (Section 11.1)."""

    model_config = {"strict": True}

    text: str
    source_language: str
    target_language: str = Field(default="en")
