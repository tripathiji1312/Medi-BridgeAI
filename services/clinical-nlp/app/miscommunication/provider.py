"""Semantic-similarity provider abstraction (same swappable-adapter rule as
speech-pipeline's ASR/MT/TTS/diarization providers).

Real implementation: SentenceTransformerSimilarityProvider (st_provider.py)
-- a small multilingual sentence-embedding model, local/self-hosted (same
"no third-party retention" rationale as every other real model in this
build). Distinct choice from speech-pipeline's NLLB: clinical-nlp doesn't
have NLLB loaded (cross-service model sharing isn't practical over the
service boundary), and NLLB is a translation model, not tuned for sentence
similarity -- a dedicated embedding model is the right tool here.
"""

from __future__ import annotations

from typing import Protocol


class SimilarityProvider(Protocol):
    def similarity(self, text_a: str, text_b: str) -> float: ...
