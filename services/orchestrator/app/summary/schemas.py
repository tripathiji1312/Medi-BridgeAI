"""Mirrors services/clinical-nlp/app/summarization/schemas.py by hand, same
pattern as every other cross-service schema in this build."""

from __future__ import annotations

from pydantic import BaseModel


class SummaryBullet(BaseModel):
    model_config = {"strict": True}

    text: str
    source_utterance_id: str


class StructuredSummary(BaseModel):
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
    discarded_ungrounded_count: int
    model_name: str
