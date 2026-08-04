"""Real similarity provider: a small multilingual sentence-embedding model
via sentence-transformers, local/self-hosted.

Import of sentence-transformers/numpy is deferred into __init__/similarity,
same pattern as speech-pipeline's real providers, so importing this module
never requires the heavy optional dependency to be installed.
"""

from __future__ import annotations

from app.miscommunication.provider import SimilarityProvider


class SentenceTransformerSimilarityProvider(SimilarityProvider):
    def __init__(
        self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - exercised only when the
            # optional heavy dependency isn't installed.
            raise RuntimeError(
                "sentence-transformers/torch are not installed. Install "
                "services/clinical-nlp/requirements-similarity.txt to use the "
                "real similarity provider; otherwise use FixtureSimilarityProvider "
                "for tests."
            ) from exc

        self._model = SentenceTransformer(model_name)

    def similarity(self, text_a: str, text_b: str) -> float:
        from sentence_transformers import util

        embeddings = self._model.encode([text_a, text_b], convert_to_tensor=True)
        cosine = float(util.cos_sim(embeddings[0], embeddings[1]).item())
        return max(0.0, min(1.0, cosine))
