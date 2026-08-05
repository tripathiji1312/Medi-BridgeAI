from __future__ import annotations

from typing import Protocol

from app.clinical_nlp.schemas import (
    EmergencyDetectionResult,
    MedicalEntity,
    MiscommunicationResult,
    RiskAssessment,
)
from app.emotion.schemas import EmotionCategory


class MiscommunicationChecker(Protocol):
    async def check(
        self, original_text: str, back_translated_text: str, language: str
    ) -> MiscommunicationResult: ...


class EntityExtractor(Protocol):
    async def extract(self, text: str, language: str) -> list[MedicalEntity]: ...


class EmergencyDetector(Protocol):
    async def detect(self, text: str, language: str) -> EmergencyDetectionResult: ...


class RiskScorer(Protocol):
    async def score(
        self,
        session_id: str,
        text: str,
        language: str,
        emotion_label: EmotionCategory | None,
        emotion_confidence: float | None,
    ) -> RiskAssessment: ...
