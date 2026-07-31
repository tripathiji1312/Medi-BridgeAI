"""Deterministic ASR test double.

Keyed by a digest of the audio bytes so tests stay deterministic and don't
require downloading/running a real model. Used by CI and any test that
doesn't specifically target the real model's behavior. Never used outside
tests -- app/main.py wires FasterWhisperASRProvider for real requests.
"""

from __future__ import annotations

import hashlib

from app.asr.provider import ASRProvider
from app.asr.schemas import TranscriptSegment


class FixtureASRProvider(ASRProvider):
    def __init__(self, fixtures: dict[str, list[TranscriptSegment]]) -> None:
        """fixtures: maps sha256(audio_bytes).hexdigest() -> expected segments."""
        self._fixtures = fixtures

    def transcribe(self, pcm16_mono: bytes, sample_rate: int) -> list[TranscriptSegment]:
        digest = hashlib.sha256(pcm16_mono).hexdigest()
        if digest not in self._fixtures:
            raise KeyError(f"No fixture registered for audio digest {digest}")
        return self._fixtures[digest]
