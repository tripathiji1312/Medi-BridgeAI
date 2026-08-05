"""Lazy singleton factory for the real emotion classifier, mirroring
app.diarization.provider_factory. The real classifier is stateless (pure
functions over each utterance's own audio) and safe to share across
sessions."""

from __future__ import annotations

import os
from functools import lru_cache

from app.emotion.provider import EmotionClassifier


@lru_cache(maxsize=1)
def get_emotion_classifier() -> EmotionClassifier:
    if os.environ.get("MEDIBRIDGE_FIXTURE_MODE") == "1":
        from app.emotion.fixture_provider import StaticEmotionClassifier

        return StaticEmotionClassifier()

    from app.emotion.prosody_classifier import ProsodyEmotionClassifier

    return ProsodyEmotionClassifier()
