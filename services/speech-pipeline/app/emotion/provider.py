"""Emotion classifier abstraction (same swappable-adapter rule as ASR/MT/TTS/
diarization). Real implementation: ProsodyEmotionClassifier
(prosody_classifier.py) -- real acoustic feature extraction (features.py) +
a deterministic, documented threshold classifier (rules.py), not a
pretrained end-to-end model. Chosen per Blueprint Section 4's own guidance
("Prosody-feature classifier ... Explainable, not a black-box end-to-end
audio LLM") and because no labeled 7-class emotion training data exists in
this project to honestly back a trained classifier head -- see
docs/PROGRESS.md for the full rationale."""

from __future__ import annotations

from typing import Protocol

from app.emotion.schemas import EmotionAssessment


class EmotionClassifier(Protocol):
    def classify(self, pcm16_mono: bytes, sample_rate: int) -> EmotionAssessment: ...
