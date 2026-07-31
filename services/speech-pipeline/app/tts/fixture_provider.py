"""Deterministic TTS test double, keyed by exact input text."""

from __future__ import annotations

import base64

from app.tts.provider import TTSProvider
from app.tts.schemas import TTSAudioSegment


class FixtureTTSProvider(TTSProvider):
    def __init__(self, fixtures: dict[str, bytes], sample_rate: int = 16_000) -> None:
        """fixtures: maps input text -> raw PCM16 audio bytes to return."""
        self._fixtures = fixtures
        self._sample_rate = sample_rate

    def synthesize(self, text: str, language: str) -> TTSAudioSegment:
        if text not in self._fixtures:
            raise KeyError(f"No fixture registered for text: {text!r}")
        audio = self._fixtures[text]
        return TTSAudioSegment(
            audio_base64=base64.b64encode(audio).decode("ascii"),
            sample_rate=self._sample_rate,
            format="pcm16",
        )
