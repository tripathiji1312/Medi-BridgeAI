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


class StaticASRProvider(ASRProvider):
    """Always returns the same canned transcript, regardless of audio
    content. Used to run the real app/main.py server deterministically for
    E2E tests and local dev without downloading faster-whisper (see
    provider_factory.py's MEDIBRIDGE_FIXTURE_MODE switch) -- NOT for unit
    tests that assert on specific inputs, where FixtureASRProvider's
    digest-keyed behavior (failing loud on an unregistered input) is the
    correct choice."""

    def __init__(
        self,
        text: str = "mujhe bukhaar hai",
        confidence: float = 0.92,
        language: str = "hi",
    ) -> None:
        self._text = text
        self._confidence = confidence
        self._language = language

    def transcribe(self, pcm16_mono: bytes, sample_rate: int) -> list[TranscriptSegment]:
        return [
            TranscriptSegment(
                text=self._text,
                is_final=True,
                confidence=self._confidence,
                start_ms=0,
                end_ms=int(len(pcm16_mono) / 2 / sample_rate * 1000),
                language=self._language,
            )
        ]
