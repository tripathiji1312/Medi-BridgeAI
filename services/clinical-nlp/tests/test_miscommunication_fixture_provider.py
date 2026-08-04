import pytest

from app.miscommunication.fixture_provider import FixtureSimilarityProvider, StaticSimilarityProvider


def test_fixture_returns_registered_score_for_matching_pair() -> None:
    provider = FixtureSimilarityProvider({("a", "b"): 0.42})

    assert provider.similarity("a", "b") == 0.42


def test_fixture_raises_for_unregistered_pair_rather_than_guessing() -> None:
    provider = FixtureSimilarityProvider({})

    with pytest.raises(KeyError):
        provider.similarity("a", "b")


def test_static_provider_returns_the_same_score_for_any_pair() -> None:
    provider = StaticSimilarityProvider(score=0.8)

    assert provider.similarity("x", "y") == provider.similarity("p", "q") == 0.8
