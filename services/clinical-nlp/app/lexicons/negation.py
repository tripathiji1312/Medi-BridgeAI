"""Curated Hindi negation markers -- deterministic, not model-derived, per
Blueprint Section 11.1's "deterministic lexicon backstop": safety-critical
signals (negation, drug names, emergency phrases) are matched against a
curated lexicon in parallel with any ML component, and on disagreement the
more conservative interpretation wins.

Not exhaustive -- covers common clinical-consultation negation forms
observed in typical Hindi speech. Flagged for expansion once real
Hindi consultation transcripts are available (see docs/PROGRESS.md).
"""

from __future__ import annotations

NEGATION_MARKERS: frozenset[str] = frozenset(
    {
        "नहीं",  # nahin -- "no"/"not"
        "ना",  # naa -- "no"/"not" (colloquial)
        "मत",  # mat -- "don't" (imperative negation)
        "बिना",  # bina -- "without"
        "कभी नहीं",  # kabhi nahin -- "never"
    }
)


def contains_negation(text: str) -> bool:
    return any(marker in text for marker in NEGATION_MARKERS)
