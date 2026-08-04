from __future__ import annotations

from pydantic import BaseModel, Field


class MiscommunicationCheckRequest(BaseModel):
    """Compares an original-language utterance against its back-translation
    (Blueprint Section 3.2 step 6: HI -> EN -> HI, compared to the original
    HI). speech-pipeline computes both texts (pure MT); this service does
    the actual consistency judgment, per AGENT_INSTRUCTIONS.md's service
    boundary table (miscommunication detection is clinical-nlp's job, not
    speech-pipeline's)."""

    model_config = {"strict": True}

    original_text: str
    back_translated_text: str
    language: str = "hi"


class MiscommunicationResult(BaseModel):
    """`reason` is never omitted -- no AI-derived value ships without its
    why (AGENT_INSTRUCTIONS.md Rule 1)."""

    model_config = {"strict": True}

    consistent: bool
    similarity_score: float = Field(ge=0.0, le=1.0)
    negation_flip_detected: bool
    reason: str
