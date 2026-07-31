"""Deterministic MT test double, keyed by exact source text. Mirrors
app.asr.fixture_provider's role -- used by tests instead of downloading/
running the real NLLB model."""

from __future__ import annotations

from app.mt.provider import MTProvider
from app.mt.schemas import TranslationSegment


class FixtureMTProvider(MTProvider):
    def __init__(self, fixtures: dict[str, str]) -> None:
        """fixtures: maps source text -> expected translated text."""
        self._fixtures = fixtures

    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationSegment:
        if text not in self._fixtures:
            raise KeyError(f"No fixture registered for source text: {text!r}")
        return TranslationSegment(
            text=self._fixtures[text],
            source_language=source_lang,
            target_language=target_lang,
        )
