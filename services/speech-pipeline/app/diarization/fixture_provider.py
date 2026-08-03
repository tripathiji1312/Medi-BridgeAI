"""Deterministic embedding test double, keyed by exact audio bytes -- mirrors
app.asr.fixture_provider's role. Lets diarizer tests exercise real clustering
logic without downloading/running the real ECAPA-TDNN model."""

from __future__ import annotations

from app.diarization.provider import SpeakerEmbeddingProvider


class FixtureEmbeddingProvider(SpeakerEmbeddingProvider):
    def __init__(self, fixtures: dict[bytes, list[float]]) -> None:
        self._fixtures = fixtures

    def embed(self, pcm16_mono: bytes, sample_rate: int) -> list[float]:
        if pcm16_mono not in self._fixtures:
            raise KeyError(f"No fixture registered for audio of length {len(pcm16_mono)}")
        return self._fixtures[pcm16_mono]


class StaticEmbeddingProvider(SpeakerEmbeddingProvider):
    """Always returns the same embedding, regardless of audio content --
    every utterance resolves to speaker_a. Used to run the real
    app/main.py server deterministically for E2E tests/local dev without
    downloading ECAPA-TDNN (see provider_factory.py's MEDIBRIDGE_FIXTURE_MODE
    switch). Not useful for testing multi-speaker clustering itself --
    app.diarization.diarizer's own tests use FixtureEmbeddingProvider with
    distinct vectors for that."""

    def embed(self, pcm16_mono: bytes, sample_rate: int) -> list[float]:
        return [1.0, 0.0, 0.0]
