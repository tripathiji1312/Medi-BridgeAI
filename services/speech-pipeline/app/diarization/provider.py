"""Speaker-embedding provider abstraction (same swappable-adapter rule as
ASR/MT/TTS). Real implementation: EcapaEmbeddingProvider (ecapa_provider.py)
-- SpeechBrain's ECAPA-TDNN (speechbrain/spkrec-ecapa-voxceleb), chosen per
the user's Phase 3 decision recorded in docs/PROGRESS.md: real ML speaker
embeddings, not pyannote.audio (its diarization pipeline is gated on
HuggingFace and needs a license-accepted token we can't provision here) and
not a manual-only toggle (explicit user preference for ML where reasonable).

This provider only extracts a fixed-length embedding per utterance; turning
a stream of embeddings into speaker labels is app.diarization.diarizer's job
-- kept separate so the (stateless, cacheable) embedding model and the
(stateful, per-session) clustering logic don't get tangled together.
"""

from __future__ import annotations

from typing import Protocol


class SpeakerEmbeddingProvider(Protocol):
    def embed(self, pcm16_mono: bytes, sample_rate: int) -> list[float]: ...
