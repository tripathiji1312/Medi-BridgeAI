"""TTS provider abstraction (same swappable-adapter rule as ASR/MT).

Real implementation: MmsTTSProvider (mms_provider.py) -- facebook/mms-tts-eng
via transformers, reusing the torch/transformers stack already required for
NLLB rather than adding a new heavy dependency family. Chosen as a natural
extension of the Phase 2 "local self-hosted model" decision already made for
MT (see docs/PROGRESS.md); flagged there as an assumption rather than a
separate question, since it's the same category of decision already
resolved this phase.
"""

from __future__ import annotations

from typing import Protocol

from app.tts.schemas import TTSAudioSegment


class TTSProvider(Protocol):
    def synthesize(self, text: str, language: str) -> TTSAudioSegment: ...
