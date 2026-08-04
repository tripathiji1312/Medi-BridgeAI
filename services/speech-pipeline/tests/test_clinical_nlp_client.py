import asyncio

import pytest

from app.clinical_nlp.http_provider import HttpMiscommunicationChecker
from app.clinical_nlp.provider_factory import get_miscommunication_checker


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    get_miscommunication_checker.cache_clear()


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
