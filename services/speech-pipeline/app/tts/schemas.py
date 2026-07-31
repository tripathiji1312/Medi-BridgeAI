from __future__ import annotations

from pydantic import BaseModel


class TTSAudioSegment(BaseModel):
    """Synthesized audio attached to a finalized TranscriptEvent's
    translation. Sent base64-encoded inline in the same JSON event rather
    than as a separate binary WS frame -- simpler client-side protocol for
    Phase 2 (single message per utterance), at a ~33% bandwidth cost versus
    raw binary framing. Revisit as a latency optimization once TTS latency
    against real (non-CPU) infra is measured -- flagged in docs/PROGRESS.md,
    not a Phase 2 blocker."""

    model_config = {"strict": True}

    audio_base64: str
    sample_rate: int
    format: str = "pcm16"
