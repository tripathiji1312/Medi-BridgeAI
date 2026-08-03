"""Lazy singleton factory for the real embedding provider, mirroring
app.asr.provider_factory. The embedding MODEL is stateless and safe to
share across sessions; per-session clustering state lives in
SpeakerDiarizer instances created fresh per WebSocket connection, not here.
"""

from __future__ import annotations

import os
from functools import lru_cache

from app.diarization.provider import SpeakerEmbeddingProvider


@lru_cache(maxsize=1)
def get_embedding_provider() -> SpeakerEmbeddingProvider:
    if os.environ.get("MEDIBRIDGE_FIXTURE_MODE") == "1":
        from app.diarization.fixture_provider import StaticEmbeddingProvider

        return StaticEmbeddingProvider()

    from app.diarization.ecapa_provider import EcapaEmbeddingProvider

    source = os.environ.get("DIARIZATION_MODEL_SOURCE", "speechbrain/spkrec-ecapa-voxceleb")
    return EcapaEmbeddingProvider(source=source)
