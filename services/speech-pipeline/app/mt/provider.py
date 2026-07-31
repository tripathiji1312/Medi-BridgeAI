"""MT provider abstraction (same swappable-adapter rule as app/asr/provider.py).

Real implementation: NLLBTranslationProvider (nllb_provider.py), chosen -- per
the user's Phase 2 decision recorded in docs/PROGRESS.md -- over IndicTrans2
(extra unvetted tooling risk) and Claude-API-based MT (third-party data
retention, Blueprint Section 6.1).
"""

from __future__ import annotations

from typing import Protocol

from app.mt.schemas import TranslationSegment


class MTProvider(Protocol):
    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationSegment: ...
