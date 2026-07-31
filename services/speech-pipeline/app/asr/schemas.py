"""Wire schemas for ASR transcript events (Blueprint Section 3.2 step 3).

Every event carries enough to satisfy the "no AI value without a reason"
rule (AGENT_INSTRUCTIONS.md Rule 1): confidence is always present, and
is_final distinguishes a stable result from one that may still change.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    model_config = {"strict": True}

    text: str
    is_final: bool
    confidence: float = Field(ge=0.0, le=1.0)
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    language: str


class TranscriptEvent(BaseModel):
    """Envelope pushed over the /ws/transcribe WebSocket, one per segment
    update. `utterance_id` lets a client correlate a partial with the final
    that supersedes it."""

    model_config = {"strict": True}

    type: str = Field(pattern="^(partial|final|error)$")
    utterance_id: str
    segment: TranscriptSegment | None = None
    error: str | None = None
    # Latency instrumentation (Blueprint Section 8 Phase 1: "Latency
    # instrumentation from day one"; Section 6.1 budget: partials <300ms).
    latency_ms: float | None = None
