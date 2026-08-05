import asyncio

import pytest

from app.memory.schemas import Utterance
from app.summary.client import HttpClinicalNlpSummarizer, get_summarizer_client


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    get_summarizer_client.cache_clear()


def test_factory_defaults_to_localhost_8002(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLINICAL_NLP_URL", raising=False)
    client = get_summarizer_client()
    assert isinstance(client, HttpClinicalNlpSummarizer)
    assert client._base_url == "http://localhost:8002"


def test_factory_reads_clinical_nlp_url_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLINICAL_NLP_URL", "http://clinical-nlp:8002/")
    client = get_summarizer_client()
    assert isinstance(client, HttpClinicalNlpSummarizer)
    assert client._base_url == "http://clinical-nlp:8002"  # trailing slash stripped


def test_raises_runtime_error_when_the_endpoint_is_unreachable() -> None:
    client = HttpClinicalNlpSummarizer(base_url="http://localhost:1", timeout_seconds=1.0)
    utterances = [Utterance(id="u1", speaker=None, original_text="fever", translated_text=None, sequence=0)]

    with pytest.raises(RuntimeError, match="clinical-nlp unavailable"):
        asyncio.run(client.summarize(utterances))
