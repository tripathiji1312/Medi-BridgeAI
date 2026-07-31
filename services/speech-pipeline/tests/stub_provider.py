"""Test-only ASR provider stub: returns a fixed segment for any input and
records every call so tests can assert on buffer durations/ordering without
needing exact byte-for-byte digest matches (which would be brittle given the
VAD's internal frame-buffering). Distinct from app.asr.fixture_provider,
which is digest-keyed and used for single-call unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.asr.schemas import TranscriptSegment


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
