from __future__ import annotations

from pydantic import BaseModel, Field


class SpeakerAssignment(BaseModel):
    """Diarization output attached to a finalized TranscriptEvent.

    `speaker_label` is content-neutral ("speaker_a"/"speaker_b") -- voice
    clustering can tell two speakers apart but cannot know which one is the
    doctor. Mapping a label to a clinical role (Doctor/Patient) is a
    human-in-the-loop UI action (Blueprint Section 1 Principle 4: AI never
    overwrites the human-readable transcript), not something inferred here.
    """

    model_config = {"strict": True}

    speaker_label: str
    confidence: float = Field(ge=0.0, le=1.0)
