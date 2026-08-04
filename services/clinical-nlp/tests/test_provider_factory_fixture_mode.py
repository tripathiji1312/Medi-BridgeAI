import pytest

from app.miscommunication.fixture_provider import StaticSimilarityProvider
from app.miscommunication.provider_factory import get_similarity_provider


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    get_similarity_provider.cache_clear()


def test_fixture_mode_selects_the_static_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEDIBRIDGE_FIXTURE_MODE", "1")
    assert isinstance(get_similarity_provider(), StaticSimilarityProvider)


def test_fixture_mode_off_by_default_attempts_the_real_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MEDIBRIDGE_FIXTURE_MODE", raising=False)
    with pytest.raises(RuntimeError, match="not installed"):
        get_similarity_provider()
