import pytest

from app.emotion.fixture_provider import FixtureEmotionClassifier, StaticEmotionClassifier
from app.emotion.schemas import EmotionAssessment


def test_fixture_classifier_returns_the_registered_assessment_for_exact_audio_bytes() -> None:
    audio = b"\x01\x02\x03\x04"
    assessment = EmotionAssessment(label="angry", confidence=0.8, reason="test fixture")
    classifier = FixtureEmotionClassifier({audio: assessment})

    result = classifier.classify(audio, 16_000)

    assert result == assessment


def test_fixture_classifier_raises_for_unregistered_audio() -> None:
    classifier = FixtureEmotionClassifier({})

    with pytest.raises(KeyError):
        classifier.classify(b"\x00\x00", 16_000)


def test_static_classifier_always_returns_neutral_regardless_of_audio() -> None:
    classifier = StaticEmotionClassifier()

    result_a = classifier.classify(b"\x01\x02", 16_000)
    result_b = classifier.classify(b"\xff\xee\xdd", 8_000)

    assert result_a.label == "neutral"
    assert result_b.label == "neutral"


def test_static_classifier_carries_the_standard_disclaimer() -> None:
    classifier = StaticEmotionClassifier()

    result = classifier.classify(b"\x01\x02", 16_000)

    assert result.disclaimer == "Estimated from voice tone, not verified."
