"""Test-only ASR provider stub: returns a fixed segment for any input and
records every call so tests can assert on buffer durations/ordering without
needing exact byte-for-byte digest matches (which would be brittle given the
VAD's internal frame-buffering). Distinct from app.asr.fixture_provider,
which is digest-keyed and used for single-call unit tests.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field

from app.asr.schemas import TranscriptSegment
from app.mt.schemas import TranslationSegment
from app.tts.schemas import TTSAudioSegment


@dataclass
class RecordingStubASRProvider:
    text: str = "test transcript"
    confidence: float = 0.9
    language: str = "hi"
    calls: list[bytes] = field(default_factory=list)

    def transcribe(self, pcm16_mono: bytes, sample_rate: int) -> list[TranscriptSegment]:
        self.calls.append(pcm16_mono)
        return [
            TranscriptSegment(
                text=self.text,
                is_final=True,
                confidence=self.confidence,
                start_ms=0,
                end_ms=int(len(pcm16_mono) / 2 / sample_rate * 1000),
                language=self.language,
            )
        ]


@dataclass
class RecordingStubMTProvider:
    translated_text: str = "stub translation"
    calls: list[str] = field(default_factory=list)
    should_fail: bool = False

    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationSegment:
        self.calls.append(text)
        if self.should_fail:
            raise RuntimeError("MT provider unavailable")
        return TranslationSegment(
            text=self.translated_text, source_language=source_lang, target_language=target_lang
        )


@dataclass
class RecordingStubTTSProvider:
    audio: bytes = b"\x01\x02\x03\x04"
    sample_rate: int = 16_000
    calls: list[str] = field(default_factory=list)
    should_fail: bool = False

    def synthesize(self, text: str, language: str) -> TTSAudioSegment:
        self.calls.append(text)
        if self.should_fail:
            raise RuntimeError("TTS provider unavailable")
        return TTSAudioSegment(
            audio_base64=base64.b64encode(self.audio).decode("ascii"),
            sample_rate=self.sample_rate,
            format="pcm16",
        )
