"""Lazy singleton factory for the real similarity provider, mirroring
speech-pipeline's provider factories."""

from __future__ import annotations

import os
from functools import lru_cache

from app.miscommunication.provider import SimilarityProvider


@lru_cache(maxsize=1)
def get_similarity_provider() -> SimilarityProvider:
    if os.environ.get("MEDIBRIDGE_FIXTURE_MODE") == "1":
        from app.miscommunication.fixture_provider import StaticSimilarityProvider

        return StaticSimilarityProvider()

    from app.miscommunication.st_provider import SentenceTransformerSimilarityProvider

    model_name = os.environ.get(
        "SIMILARITY_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    return SentenceTransformerSimilarityProvider(model_name=model_name)
