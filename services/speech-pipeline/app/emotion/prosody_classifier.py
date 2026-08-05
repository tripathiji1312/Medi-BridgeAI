"""Real emotion classifier: real acoustic feature extraction (features.py)
+ deterministic classification rules (rules.py). Import of numpy is
deferred into __init__, same pattern as every other real provider in this
build, so importing this module never requires the dependency to be
installed."""

from __future__ import annotations

from app.emotion.provider import EmotionClassifier
from app.emotion.schemas import EmotionAssessment


class ProsodyEmotionClassifier(EmotionClassifier):
    def __init__(self) -> None:
        try:
            import numpy  # noqa: F401
        except ImportError as exc:  # pragma: no cover - exercised only when the
            # optional dependency isn't installed.
            raise RuntimeError(
                "numpy is not installed. Install "
                "services/speech-pipeline/requirements-emotion.txt to use "
                "the real emotion classifier; otherwise use "
                "StaticEmotionClassifier for MEDIBRIDGE_FIXTURE_MODE."
            ) from exc

    def classify(self, pcm16_mono: bytes, sample_rate: int) -> EmotionAssessment:
        from app.emotion.features import extract_prosody_features
        from app.emotion.rules import classify_emotion

        features = extract_prosody_features(pcm16_mono, sample_rate)
        return classify_emotion(features)
