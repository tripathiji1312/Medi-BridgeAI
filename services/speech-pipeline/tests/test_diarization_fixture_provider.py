import pytest

from app.diarization.fixture_provider import FixtureEmbeddingProvider


def test_returns_registered_embedding_for_matching_audio() -> None:
    provider = FixtureEmbeddingProvider({b"audio-a": [1.0, 0.0]})

    assert provider.embed(b"audio-a", 16_000) == [1.0, 0.0]


def test_raises_for_unregistered_audio_rather_than_silently_returning_a_zero_vector() -> None:
    provider = FixtureEmbeddingProvider({})

    with pytest.raises(KeyError):
        provider.embed(b"unregistered", 16_000)
