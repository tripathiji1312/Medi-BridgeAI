"""Miscommunication detection: combines a deterministic negation-lexicon
check with a semantic-similarity model, per Blueprint Section 11.1's
"deterministic lexicon backstop" rule -- on disagreement between the
lexicon and the model, the more conservative (safety-favoring)
interpretation wins. Here that means a negation flip is a hard fail
regardless of how similar the two texts otherwise look.
"""

from __future__ import annotations

from app.lexicons.negation import contains_negation
from app.miscommunication.provider import SimilarityProvider
from app.miscommunication.schemas import MiscommunicationResult

# Below this cosine-similarity score, back-translation is judged to have
# diverged from the original. Not tuned against a labeled gold set yet --
# qualitative starting point, flagged in docs/PROGRESS.md for revisit once
# real multi-turn consultation transcripts are available.
SIMILARITY_CONSISTENT_THRESHOLD = 0.75


class MiscommunicationDetector:
    def __init__(self, similarity_provider: SimilarityProvider) -> None:
        self._similarity_provider = similarity_provider

    def check(self, original_text: str, back_translated_text: str) -> MiscommunicationResult:
        similarity = self._similarity_provider.similarity(original_text, back_translated_text)
        negation_flip = contains_negation(original_text) != contains_negation(back_translated_text)

        if negation_flip:
            # Lexicon backstop wins even if the model reports high
            # similarity -- negation flips are exactly the kind of
            # semantically-small-but-clinically-critical error embedding
            # similarity can miss (Blueprint Section 7.1: "no fever" vs
            # "fever" must not be flattened together).
            return MiscommunicationResult(
                consistent=False,
                similarity_score=similarity,
                negation_flip_detected=True,
                reason=(
                    "Negation mismatch between the original and its back-translation "
                    "-- possible meaning flip (e.g. 'not diabetic' vs 'diabetic')."
                ),
            )

        if similarity < SIMILARITY_CONSISTENT_THRESHOLD:
            return MiscommunicationResult(
                consistent=False,
                similarity_score=similarity,
                negation_flip_detected=False,
                reason=(
                    f"Back-translation diverges from the original "
                    f"(similarity {similarity:.2f} < {SIMILARITY_CONSISTENT_THRESHOLD})."
                ),
            )

        return MiscommunicationResult(
            consistent=True,
            similarity_score=similarity,
            negation_flip_detected=False,
            reason=f"Back-translation matches the original closely (similarity {similarity:.2f}).",
        )
