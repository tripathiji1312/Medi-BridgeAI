from app.confidence.scoring import compute_confidence_v2, confidence_band


def test_composite_averages_asr_and_back_translation_signals() -> None:
    assert compute_confidence_v2(asr_confidence=1.0, back_translation_similarity=1.0) == 1.0
    assert compute_confidence_v2(asr_confidence=0.0, back_translation_similarity=0.0) == 0.0
    assert compute_confidence_v2(asr_confidence=1.0, back_translation_similarity=0.0) == 0.5


def test_confidence_band_matches_blueprint_thresholds() -> None:
    assert confidence_band(0.85) == "green"
    assert confidence_band(1.0) == "green"
    assert confidence_band(0.84) == "yellow"
    assert confidence_band(0.60) == "yellow"
    assert confidence_band(0.59) == "red"
    assert confidence_band(0.0) == "red"
