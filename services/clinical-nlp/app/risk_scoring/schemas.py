from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

RiskLevel = Literal["low", "medium", "high"]

# Mirrors services/speech-pipeline/app/emotion/schemas.py's EmotionCategory --
# clinical-nlp doesn't compute emotion (that's speech-pipeline's job, audio
# processing is outside this service's boundary per AGENT_INSTRUCTIONS.md
# Section 2), but risk scoring takes it as one input, so this service needs
# to know the same category set to interpret it. Manually mirrored across
# the service boundary, same pattern as MedicalEntity/TranscriptEvent.
EmotionCategory = Literal["calm", "anxious", "fearful", "stressed", "angry", "happy", "neutral"]


class RiskScoreRequest(BaseModel):
    model_config = {"strict": True}

    session_id: str
    text: str
    language: str = "hi"
    emotion_label: EmotionCategory | None = None
    emotion_confidence: float | None = None


class RiskAssessment(BaseModel):
    """`level` is the hysteresis-smoothed value actually shown to the
    clinician (Blueprint Section 7.3: "must use hysteresis/smoothing, not
    instant flips that alarm-fatigue the clinician"). `raw_level` is what
    this single utterance alone would score, included so the smoothing
    itself is auditable rather than a black box. `reason` always names the
    concrete signals that drove the score (Blueprint Section 1 Principle 2)
    -- never a bare Low/Medium/High label."""

    model_config = {"strict": True}

    level: RiskLevel
    raw_level: RiskLevel
    reason: str
    emergency_triggered: bool
    symptom_count: int
    lexicon_version: str
