import pytest

from app.mt.fixture_provider import FixtureMTProvider, StaticMTProvider


def test_returns_registered_translation_for_matching_text() -> None:
    provider = FixtureMTProvider({"mujhe bukhaar hai": "I have a fever"})

    result = provider.translate("mujhe bukhaar hai", "hi", "en")

    assert result.text == "I have a fever"
    assert result.source_language == "hi"
    assert result.target_language == "en"


def test_raises_for_unregistered_text_rather_than_silently_returning_empty() -> None:
    provider = FixtureMTProvider({})

    with pytest.raises(KeyError):
        provider.translate("unregistered text", "hi", "en")


def test_static_provider_returns_the_same_canned_translation_for_any_text() -> None:
    provider = StaticMTProvider(translated_text="fixed translation")

    result = provider.translate("any Hindi text at all", "hi", "en")

    assert result.text == "fixed translation"
    assert result.target_language == "en"
