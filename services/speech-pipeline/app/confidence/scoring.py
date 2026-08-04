"""Confidence score v2: composite of ASR confidence and back-translation
agreement (Blueprint Section 2.2: "composite of ASR confidence, MT model
logprob/self-consistency, and back-translation agreement"). MT
logprob/self-consistency isn't included yet -- NLLB's HF `generate()` API
doesn't cheaply expose per-sequence logprobs through the abstraction this
build uses (see docs/PROGRESS.md); the two-signal composite here is a
real, honest subset, not the full three-signal formula, and is documented
as such rather than silently presented as complete.

Bands mirror packages/design-tokens/index.ts's confidenceBand() exactly --
Blueprint Section 2.2: Green >=85, Yellow 60-84, Red <60 (on the 0-100
scale; this module works in 0-1 to match every other confidence value in
the codebase, converting only for the band cutoffs).
"""

from __future__ import annotations

from typing import Literal

ConfidenceBand = Literal["green", "yellow", "red"]

ASR_WEIGHT = 0.5
BACK_TRANSLATION_WEIGHT = 0.5


def compute_confidence_v2(asr_confidence: float, back_translation_similarity: float) -> float:
    composite = asr_confidence * ASR_WEIGHT + back_translation_similarity * BACK_TRANSLATION_WEIGHT
    return max(0.0, min(1.0, composite))


def confidence_band(score_0_to_1: float) -> ConfidenceBand:
    score_pct = score_0_to_1 * 100
    if score_pct >= 85:
        return "green"
    if score_pct >= 60:
        return "yellow"
    return "red"
