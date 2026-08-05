"""Factory for the miscommunication checker. Unlike the ML provider
factories, this one isn't lazy-behind-an-import (httpx is always
installed) -- MEDIBRIDGE_FIXTURE_MODE here just points at wherever the
fixture-mode clinical-nlp instance is running instead of swapping the
implementation, since the real implementation *is* just an HTTP call."""

from __future__ import annotations

import os
from functools import lru_cache

from app.clinical_nlp.http_provider import (
    HttpEmergencyDetector,
    HttpEntityExtractor,
    HttpMiscommunicationChecker,
    HttpRiskScorer,
)
from app.clinical_nlp.provider import EmergencyDetector, EntityExtractor, MiscommunicationChecker, RiskScorer


@lru_cache(maxsize=1)
def get_miscommunication_checker() -> MiscommunicationChecker:
    base_url = os.environ.get("CLINICAL_NLP_URL", "http://localhost:8002")
    return HttpMiscommunicationChecker(base_url=base_url)


@lru_cache(maxsize=1)
def get_entity_extractor() -> EntityExtractor:
    base_url = os.environ.get("CLINICAL_NLP_URL", "http://localhost:8002")
    return HttpEntityExtractor(base_url=base_url)


@lru_cache(maxsize=1)
def get_emergency_detector() -> EmergencyDetector:
    base_url = os.environ.get("CLINICAL_NLP_URL", "http://localhost:8002")
    return HttpEmergencyDetector(base_url=base_url)


@lru_cache(maxsize=1)
def get_risk_scorer() -> RiskScorer:
    base_url = os.environ.get("CLINICAL_NLP_URL", "http://localhost:8002")
    return HttpRiskScorer(base_url=base_url)
