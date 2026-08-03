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
