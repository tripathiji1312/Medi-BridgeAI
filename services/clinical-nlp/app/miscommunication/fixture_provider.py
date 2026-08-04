"""Deterministic similarity test doubles, mirroring speech-pipeline's
Fixture*/Static* provider split."""

from __future__ import annotations

from app.miscommunication.provider import SimilarityProvider


class FixtureSimilarityProvider(SimilarityProvider):
    def __init__(self, fixtures: dict[tuple[str, str], float]) -> None:
        """fixtures: maps (text_a, text_b) -> expected similarity score."""
        self._fixtures = fixtures

    def similarity(self, text_a: str, text_b: str) -> float:
        key = (text_a, text_b)
        if key not in self._fixtures:
            raise KeyError(f"No fixture registered for pair: {key!r}")
        return self._fixtures[key]


class StaticSimilarityProvider(SimilarityProvider):
    """Always returns the same similarity score, regardless of input --
    used to run the real app/main.py server deterministically for E2E
    tests/local dev (see provider_factory.py's MEDIBRIDGE_FIXTURE_MODE
    switch)."""

    def __init__(self, score: float = 0.9) -> None:
        self._score = score

    def similarity(self, text_a: str, text_b: str) -> float:
        return self._score
