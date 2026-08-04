from app.miscommunication.detector import MiscommunicationDetector
from app.miscommunication.fixture_provider import FixtureSimilarityProvider


def test_high_similarity_with_no_negation_is_consistent() -> None:
    provider = FixtureSimilarityProvider({("मुझे बुखार है", "मुझे बुखार है"): 0.95})
    detector = MiscommunicationDetector(provider)

    result = detector.check("मुझे बुखार है", "मुझे बुखार है")

    assert result.consistent is True
    assert result.negation_flip_detected is False
    assert result.similarity_score == 0.95
    assert "matches" in result.reason.lower()


def test_low_similarity_is_flagged_inconsistent_with_a_reason() -> None:
    provider = FixtureSimilarityProvider({("मुझे बुखार है", "मुझे सिरदर्द है"): 0.3})
    detector = MiscommunicationDetector(provider)

    result = detector.check("मुझे बुखार है", "मुझे सिरदर्द है")

    assert result.consistent is False
    assert result.negation_flip_detected is False
    assert "diverges" in result.reason.lower()


def test_negation_flip_is_a_hard_fail_even_with_high_similarity() -> None:
    # Deterministic lexicon backstop wins over the model (Blueprint Section
    # 11.1): a negation flip must never be waved through just because the
    # embedding model reports the two texts as similar.
    provider = FixtureSimilarityProvider({("मुझे बुखार है", "मुझे बुखार नहीं है"): 0.97})
    detector = MiscommunicationDetector(provider)

    result = detector.check("मुझे बुखार है", "मुझे बुखार नहीं है")

    assert result.consistent is False
    assert result.negation_flip_detected is True
    assert result.similarity_score == 0.97  # score is still reported, not discarded
    assert "negation" in result.reason.lower()


def test_negation_present_in_both_texts_is_not_a_flip() -> None:
    provider = FixtureSimilarityProvider({("मुझे बुखार नहीं है", "मुझे बुखार नहीं है"): 0.95})
    detector = MiscommunicationDetector(provider)

    result = detector.check("मुझे बुखार नहीं है", "मुझे बुखार नहीं है")

    assert result.negation_flip_detected is False
    assert result.consistent is True
