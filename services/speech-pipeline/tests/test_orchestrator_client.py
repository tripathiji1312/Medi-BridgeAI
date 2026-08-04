import asyncio

import pytest

from app.orchestrator_client import HttpOrchestratorClient
from app.orchestrator_client_factory import get_orchestrator_client


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    get_orchestrator_client.cache_clear()


def test_factory_defaults_to_localhost_8004(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ORCHESTRATOR_URL", raising=False)
    client = get_orchestrator_client()
    assert isinstance(client, HttpOrchestratorClient)
    assert client._base_url == "http://localhost:8004"


def test_factory_reads_orchestrator_url_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORCHESTRATOR_URL", "http://orchestrator:8004/")
    client = get_orchestrator_client()
    assert isinstance(client, HttpOrchestratorClient)
    assert client._base_url == "http://orchestrator:8004"  # trailing slash stripped


def test_post_utterance_does_not_raise_when_orchestrator_is_unreachable() -> None:
    # Unlike the miscommunication checker (whose caller needs to know it
    # failed to attach *_error), recording an utterance is a background
    # side effect with no client-visible outcome -- the client swallows
    # its own errors internally rather than raising, per its docstring.
    client = HttpOrchestratorClient(base_url="http://localhost:1", timeout_seconds=1.0)
    asyncio.run(client.post_utterance("s1", "speaker_a", "text", "translated"))
