from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MiscommunicationResult(BaseModel):
    """Mirrors services/clinical-nlp/app/miscommunication/schemas.py
    MiscommunicationResult -- kept in parity by hand, same as every other
    cross-service schema in this build (see packages/shared-types for the
    TS-side equivalent pattern)."""

    model_config = {"strict": True}

    consistent: bool
    similarity_score: float = Field(ge=0.0, le=1.0)
    negation_flip_detected: bool
    reason: str


EntityCategory = Literal["symptom", "disease", "medication", "allergy", "vital_sign", "procedure"]


class MedicalEntity(BaseModel):
    """Mirrors services/clinical-nlp/app/ner/schemas.py MedicalEntity."""

    model_config = {"strict": True}

    text: str
    category: EntityCategory
    canonical_name: str
    canonical_code: str | None
    definition: str
    confidence: float = Field(ge=0.0, le=1.0)
    start_char: int = Field(ge=0)
    end_char: int = Field(ge=0)
    is_fuzzy_match: bool


class EmergencyDetectionResult(BaseModel):
    """Mirrors services/clinical-nlp/app/emergency_detector/schemas.py
    EmergencyDetectionResponse."""

    model_config = {"strict": True}

    alert: bool
    matches: list[MedicalEntity]
    reason: str | None
    lexicon_version: str


RiskLevel = Literal["low", "medium", "high"]


class RiskAssessment(BaseModel):
    """Mirrors services/clinical-nlp/app/risk_scoring/schemas.py
    RiskAssessment."""

    model_config = {"strict": True}

    level: RiskLevel
    raw_level: RiskLevel
    reason: str
    emergency_triggered: bool
    symptom_count: int
    lexicon_version: str
