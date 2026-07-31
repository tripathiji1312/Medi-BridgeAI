"""ASR provider abstraction (AGENT_INSTRUCTIONS.md Rule: "All AI/ML model
interfaces must sit behind an abstraction/adapter, so providers are
swappable without touching business logic" -- Blueprint Section 6.2).

Two implementations exist:
- FasterWhisperASRProvider (asr/faster_whisper_provider.py): real local
  open-source model, chosen over a commercial API per the Phase 1 decision
  logged in docs/PROGRESS.md (zero third-party data retention, Blueprint
  Section 6.1 hard constraint).
- FixtureASRProvider (asr/fixture_provider.py): deterministic test double
  used in CI/unit tests so ASR tests don't depend on downloading model
  weights or on non-deterministic model output.
"""

from __future__ import annotations

from typing import Protocol

from app.asr.schemas import TranscriptSegment


class ASRProvider(Protocol):
    """Batch transcription of a complete audio buffer.

    Phase 1 scope is "pre-recorded fixtures before live mic" (Blueprint
    Section 8), so the contract is batch-in/segments-out; the WebSocket
    layer (app/asr/session.py) is what turns this into partial/final
    streaming events as audio arrives incrementally.
    """

    def transcribe(self, pcm16_mono: bytes, sample_rate: int) -> list[TranscriptSegment]:
        """pcm16_mono: little-endian 16-bit PCM, single channel."""
        ...
