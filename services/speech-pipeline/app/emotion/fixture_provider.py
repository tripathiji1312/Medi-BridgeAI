"""Deterministic emotion test doubles -- mirrors app.diarization's
Fixture/Static split. This repo has no labeled emotional-speech audio, so
FixtureEmotionClassifier is keyed by exact audio bytes (like
FixtureEmbeddingProvider) rather than by any real emotional content."""

from __future__ import annotations

from app.emotion.provider import EmotionClassifier
from app.emotion.schemas import EmotionAssessment


class FixtureEmotionClassifier(EmotionClassifier):
    def __init__(self, fixtures: dict[bytes, EmotionAssessment]) -> None:
        self._fixtures = fixtures

    def classify(self, pcm16_mono: bytes, sample_rate: int) -> EmotionAssessment:
        if pcm16_mono not in self._fixtures:
            raise KeyError(f"No fixture registered for audio of length {len(pcm16_mono)}")
        return self._fixtures[pcm16_mono]


class StaticEmotionClassifier(EmotionClassifier):
    """Always returns 'neutral' regardless of audio content -- used to run
    the real server deterministically under MEDIBRIDGE_FIXTURE_MODE.
    Emotion has no heavy model to download in the first place (the real
    provider is pure numpy DSP), but this keeps parity with every other
    Static*Provider so E2E output stays fully deterministic without
    depending on the specific fixture audio's actual prosody."""

    def classify(self, pcm16_mono: bytes, sample_rate: int) -> EmotionAssessment:
        return EmotionAssessment(
            label="neutral",
            confidence=0.5,
            reason="Fixture mode: deterministic canned response, not derived from real audio.",
        )
