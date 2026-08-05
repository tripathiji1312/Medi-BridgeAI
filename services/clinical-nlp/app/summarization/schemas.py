from __future__ import annotations

from pydantic import BaseModel


class SummaryUtterance(BaseModel):
    """One turn of the conversation, as already recorded by orchestrator
    (services/orchestrator/app/memory/schemas.py Utterance) -- this service
    doesn't store transcripts itself, so the caller (orchestrator) sends
    them for each summarization request."""

    model_config = {"strict": True}

    utterance_id: str
    speaker: str | None
    original_text: str
    translated_text: str | None


class SummaryBullet(BaseModel):
    """`source_utterance_id` is mandatory, not optional -- Blueprint Section
    11.1: "every ... summary bullet must carry a reference to the exact
    transcript span it came from. If an LLM-based extractor cannot produce
    a valid span match, the item is discarded, not shown." A bullet with no
    grounded source never reaches this model (see grounding.py)."""

    model_config = {"strict": True}

    text: str
    source_utterance_id: str


class StructuredSummary(BaseModel):
    """SOAP-like structure mapped onto the blueprint's brief fields
    (Blueprint Section 2.2: "AI Meeting Summary"). `diagnoses_mentioned` is
    named deliberately, not `diagnoses` -- this is a transcription of what
    was *said*, never an AI-originated diagnosis (Section 1 Principle 5:
    "not a diagnostic system"). `objective` is genuinely often empty (no
    vitals/observations were necessarily stated) -- an empty list here is
    the correct, honest output, not a sign of failure."""

    model_config = {"strict": True}

    patient_info: str | None
    complaints: list[SummaryBullet]
    symptoms: list[SummaryBullet]
    objective: list[SummaryBullet]
    diagnoses_mentioned: list[SummaryBullet]
    medications: list[SummaryBullet]
    recommendations: list[SummaryBullet]
    action_items: list[SummaryBullet]
    follow_up: list[SummaryBullet]
    # Transparency, not hidden (Blueprint Section 1 Principle 2): how many
    # bullets the model proposed but this service discarded for failing
    # grounding validation.
    discarded_ungrounded_count: int
    model_name: str


class SummarizeRequest(BaseModel):
    model_config = {"strict": True}

    utterances: list[SummaryUtterance]
