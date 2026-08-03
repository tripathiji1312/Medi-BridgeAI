import pytest

from app.diarization.fixture_provider import FixtureEmbeddingProvider, StaticEmbeddingProvider


def test_returns_registered_embedding_for_matching_audio() -> None:
    provider = FixtureEmbeddingProvider({b"audio-a": [1.0, 0.0]})

    assert provider.embed(b"audio-a", 16_000) == [1.0, 0.0]


def test_raises_for_unregistered_audio_rather_than_silently_returning_a_zero_vector() -> None:
    provider = FixtureEmbeddingProvider({})

    with pytest.raises(KeyError):
        provider.embed(b"unregistered", 16_000)


def test_static_provider_returns_the_same_embedding_for_any_audio() -> None:
    provider = StaticEmbeddingProvider()

    assert provider.embed(b"audio-a", 16_000) == provider.embed(b"totally different audio", 16_000)
