from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Blueprint Section 2.2: "7-class (Calm, Anxious, Fearful, Stressed, Angry,
# Happy, Neutral)".
EmotionCategory = Literal["calm", "anxious", "fearful", "stressed", "angry", "happy", "neutral"]

EMOTION_DISCLAIMER = "Estimated from voice tone, not verified."


class EmotionAssessment(BaseModel):
    """`reason` always names the acoustic pattern that drove the label
    (Blueprint Section 1 Principle 2 -- never a bare label), and
    `disclaimer` is always attached, per Blueprint Section 2.2's explicit
    "estimated from voice tone, not verified" requirement."""

    model_config = {"strict": True}

    label: EmotionCategory
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    disclaimer: str = EMOTION_DISCLAIMER
