from __future__ import annotations

from typing import Protocol

from app.clinical_nlp.schemas import MedicalEntity, MiscommunicationResult


class MiscommunicationChecker(Protocol):
    async def check(
        self, original_text: str, back_translated_text: str, language: str
    ) -> MiscommunicationResult: ...


class EntityExtractor(Protocol):
    async def extract(self, text: str, language: str) -> list[MedicalEntity]: ...
