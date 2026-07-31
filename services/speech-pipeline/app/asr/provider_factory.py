"""Default real-provider factory for production wiring (app/main.py).

Deferred/lazy so importing this module never requires faster-whisper to be
installed -- only calling get_asr_provider() does, and callers (the
WebSocket route) catch RuntimeError to fail loud with a client-visible
degraded-mode message instead of crashing the process
(Blueprint Section 6.1: "no single ML service outage can crash the session").
"""

from __future__ import annotations

import os
from functools import lru_cache

from app.asr.provider import ASRProvider


@lru_cache(maxsize=1)
def get_asr_provider() -> ASRProvider:
    from app.asr.faster_whisper_provider import FasterWhisperASRProvider

    model_size = os.environ.get("ASR_MODEL_SIZE", "small")
    return FasterWhisperASRProvider(model_size=model_size)
