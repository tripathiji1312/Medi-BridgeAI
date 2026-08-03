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


class StaticMTProvider(MTProvider):
    """Always returns the same canned translation, regardless of input text.
    Used to run the real app/main.py server deterministically for E2E tests/
    local dev without downloading NLLB (see provider_factory.py's
    MEDIBRIDGE_FIXTURE_MODE switch)."""

    def __init__(self, translated_text: str = "I have a fever") -> None:
        self._translated_text = translated_text

    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationSegment:
        return TranslationSegment(
            text=self._translated_text,
            source_language=source_lang,
            target_language=target_lang,
        )
