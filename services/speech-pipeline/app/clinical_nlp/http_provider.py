"""Real HTTP clients for clinical-nlp's endpoints. httpx is a base runtime
dependency here (not behind a requirements-*.txt extra like the ML
providers) since it's just an HTTP client, not a heavy model."""

from __future__ import annotations

import httpx
from pydantic import TypeAdapter

from app.clinical_nlp.provider import EmergencyDetector, EntityExtractor, MiscommunicationChecker, RiskScorer
from app.clinical_nlp.schemas import (
    EmergencyDetectionResult,
    MedicalEntity,
    MiscommunicationResult,
    RiskAssessment,
)
from app.emotion.schemas import EmotionCategory

_ENTITY_LIST_ADAPTER: TypeAdapter[list[MedicalEntity]] = TypeAdapter(list[MedicalEntity])


class HttpMiscommunicationChecker(MiscommunicationChecker):
    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def check(
        self, original_text: str, back_translated_text: str, language: str
    ) -> MiscommunicationResult:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            try:
                response = await client.post(
                    f"{self._base_url}/miscommunication/check",
                    json={
                        "original_text": original_text,
                        "back_translated_text": back_translated_text,
                        "language": language,
                    },
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise RuntimeError(f"clinical-nlp unavailable: {exc}") from exc
        return MiscommunicationResult.model_validate(response.json())


class HttpEntityExtractor(EntityExtractor):
    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def extract(self, text: str, language: str) -> list[MedicalEntity]:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            try:
                response = await client.post(
                    f"{self._base_url}/entities/extract",
                    json={"text": text, "language": language},
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise RuntimeError(f"clinical-nlp unavailable: {exc}") from exc
        return _ENTITY_LIST_ADAPTER.validate_python(response.json()["entities"])


class HttpEmergencyDetector(EmergencyDetector):
    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def detect(self, text: str, language: str) -> EmergencyDetectionResult:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            try:
                response = await client.post(
                    f"{self._base_url}/emergency/detect",
                    json={"text": text, "language": language},
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise RuntimeError(f"clinical-nlp unavailable: {exc}") from exc
        return EmergencyDetectionResult.model_validate(response.json())


class HttpRiskScorer(RiskScorer):
    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def score(
        self,
        session_id: str,
        text: str,
        language: str,
        emotion_label: EmotionCategory | None,
        emotion_confidence: float | None,
    ) -> RiskAssessment:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            try:
                response = await client.post(
                    f"{self._base_url}/risk/score",
                    json={
                        "session_id": session_id,
                        "text": text,
                        "language": language,
                        "emotion_label": emotion_label,
                        "emotion_confidence": emotion_confidence,
                    },
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise RuntimeError(f"clinical-nlp unavailable: {exc}") from exc
        return RiskAssessment.model_validate(response.json())
