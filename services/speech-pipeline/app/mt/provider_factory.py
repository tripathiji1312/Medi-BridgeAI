"""Lazy singleton factory for the real MT provider, mirroring
app.asr.provider_factory. Callers catch RuntimeError to degrade gracefully
(Blueprint Section 6.1/7.2: translation-service-unreachable falls back to
raw transcript only, not a crash)."""

from __future__ import annotations

import os
from functools import lru_cache

from app.mt.provider import MTProvider


@lru_cache(maxsize=1)
def get_mt_provider() -> MTProvider:
    from app.mt.nllb_provider import NLLBTranslationProvider

    model_name = os.environ.get("MT_MODEL_NAME", "facebook/nllb-200-distilled-600M")
    return NLLBTranslationProvider(model_name=model_name)
