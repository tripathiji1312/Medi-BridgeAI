from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

TimelineEventType = Literal[
    "symptom_mentioned",
    "medication_mentioned",
    "alert_triggered",
    "alert_dismissed",
    "risk_level_changed",
]


class AddTimelineEventRequest(BaseModel):
    model_config = {"strict": True}

    type: TimelineEventType
    description: str
    source_utterance_id: str | None = None


class TimelineEvent(BaseModel):
    """`timestamp` is real wall-clock time (ISO 8601, UTC), set server-side
    at append time -- not derived from audio-relative start_ms/end_ms,
    which are meaningless outside their own utterance. A session timeline
    needs actual chronological ordering across utterances, alerts, and risk
    changes, which only a real clock timestamp gives."""

    model_config = {"strict": True}

    id: str
    type: TimelineEventType
    description: str
    source_utterance_id: str | None
    timestamp: str
