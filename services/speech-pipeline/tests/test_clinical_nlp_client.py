import asyncio

import pytest

from app.clinical_nlp.http_provider import (
    HttpEmergencyDetector,
    HttpEntityExtractor,
    HttpMiscommunicationChecker,
    HttpRiskScorer,
)
from app.clinical_nlp.provider_factory import (
    get_emergency_detector,
    get_entity_extractor,
    get_miscommunication_checker,
    get_risk_scorer,
)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    get_miscommunication_checker.cache_clear()
    get_entity_extractor.cache_clear()
    get_emergency_detector.cache_clear()
    get_risk_scorer.cache_clear()


def test_factory_defaults_to_localhost_8002(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLINICAL_NLP_URL", raising=False)
    checker = get_miscommunication_checker()
    assert isinstance(checker, HttpMiscommunicationChecker)
    assert checker._base_url == "http://localhost:8002"


def test_factory_reads_clinical_nlp_url_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLINICAL_NLP_URL", "http://clinical-nlp:8002/")
    checker = get_miscommunication_checker()
    assert isinstance(checker, HttpMiscommunicationChecker)
    assert checker._base_url == "http://clinical-nlp:8002"  # trailing slash stripped


def test_raises_runtime_error_when_the_endpoint_is_unreachable() -> None:
    checker = HttpMiscommunicationChecker(base_url="http://localhost:1", timeout_seconds=1.0)
    with pytest.raises(RuntimeError, match="clinical-nlp unavailable"):
        asyncio.run(checker.check("a", "b", "hi"))


def test_entity_extractor_factory_defaults_to_localhost_8002(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLINICAL_NLP_URL", raising=False)
    extractor = get_entity_extractor()
    assert isinstance(extractor, HttpEntityExtractor)
    assert extractor._base_url == "http://localhost:8002"


def test_entity_extractor_raises_runtime_error_when_the_endpoint_is_unreachable() -> None:
    extractor = HttpEntityExtractor(base_url="http://localhost:1", timeout_seconds=1.0)
    with pytest.raises(RuntimeError, match="clinical-nlp unavailable"):
        asyncio.run(extractor.extract("मुझे बुखार है", "hi"))


def test_emergency_detector_factory_defaults_to_localhost_8002(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLINICAL_NLP_URL", raising=False)
    detector = get_emergency_detector()
    assert isinstance(detector, HttpEmergencyDetector)
    assert detector._base_url == "http://localhost:8002"


def test_emergency_detector_raises_runtime_error_when_the_endpoint_is_unreachable() -> None:
    detector = HttpEmergencyDetector(base_url="http://localhost:1", timeout_seconds=1.0)
    with pytest.raises(RuntimeError, match="clinical-nlp unavailable"):
        asyncio.run(detector.detect("chest pain", "en"))


def test_risk_scorer_factory_defaults_to_localhost_8002(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLINICAL_NLP_URL", raising=False)
    scorer = get_risk_scorer()
    assert isinstance(scorer, HttpRiskScorer)
    assert scorer._base_url == "http://localhost:8002"


def test_risk_scorer_raises_runtime_error_when_the_endpoint_is_unreachable() -> None:
    scorer = HttpRiskScorer(base_url="http://localhost:1", timeout_seconds=1.0)
    with pytest.raises(RuntimeError, match="clinical-nlp unavailable"):
        asyncio.run(scorer.score("s1", "I have a fever", "en", None, None))
