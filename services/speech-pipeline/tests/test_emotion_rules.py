"""Tests classify_emotion() directly against constructed ProsodyFeatures --
deliberately not routed through real audio here, so each branch of the
decision tree can be exercised precisely and independently of the feature
extractor's own correctness (that's test_emotion_features.py's job)."""

from __future__ import annotations

from app.emotion.features import ProsodyFeatures
from app.emotion.rules import classify_emotion


def test_insufficient_voiced_signal_returns_neutral_with_low_confidence() -> None:
    features = ProsodyFeatures(pitch_mean_hz=0.0, pitch_std_hz=0.0, energy_mean=0.0, energy_std=0.0, voiced_ratio=0.05)

    result = classify_emotion(features)

    assert result.label == "neutral"
    assert result.confidence <= 0.3
    assert "Not enough voiced speech" in result.reason


def test_loud_and_highly_variable_pitch_is_angry() -> None:
    features = ProsodyFeatures(
        pitch_mean_hz=200.0, pitch_std_hz=90.0, energy_mean=0.15, energy_std=0.05, voiced_ratio=0.8
    )

    result = classify_emotion(features)

    assert result.label == "angry"
    assert "Loud" in result.reason and "variable pitch" in result.reason


def test_high_pitch_low_volume_is_fearful() -> None:
    features = ProsodyFeatures(
        pitch_mean_hz=230.0, pitch_std_hz=10.0, energy_mean=0.01, energy_std=0.002, voiced_ratio=0.6
    )

    result = classify_emotion(features)

    assert result.label == "fearful"
    assert "low volume" in result.reason


def test_variable_pitch_with_little_pausing_is_anxious() -> None:
    features = ProsodyFeatures(
        pitch_mean_hz=180.0, pitch_std_hz=50.0, energy_mean=0.05, energy_std=0.01, voiced_ratio=0.85
    )

    result = classify_emotion(features)

    assert result.label == "anxious"


def test_loud_and_higher_pitched_is_happy_with_capped_confidence() -> None:
    features = ProsodyFeatures(
        pitch_mean_hz=200.0, pitch_std_hz=5.0, energy_mean=0.12, energy_std=0.01, voiced_ratio=0.6
    )

    result = classify_emotion(features)

    assert result.label == "happy"
    # Explicitly capped lower than other branches -- prosody alone can't
    # reliably distinguish positive from negative high-arousal states.
    assert result.confidence <= 0.55
    assert "can also indicate anger" in result.reason


def test_moderate_variability_is_stressed() -> None:
    features = ProsodyFeatures(
        pitch_mean_hz=170.0, pitch_std_hz=35.0, energy_mean=0.03, energy_std=0.007, voiced_ratio=0.5
    )

    result = classify_emotion(features)

    assert result.label == "stressed"


def test_steady_pitch_and_loudness_is_calm() -> None:
    features = ProsodyFeatures(
        pitch_mean_hz=160.0, pitch_std_hz=5.0, energy_mean=0.03, energy_std=0.001, voiced_ratio=0.5
    )

    result = classify_emotion(features)

    assert result.label == "calm"


def test_unremarkable_features_default_to_neutral() -> None:
    features = ProsodyFeatures(
        pitch_mean_hz=165.0, pitch_std_hz=18.0, energy_mean=0.03, energy_std=0.004, voiced_ratio=0.5
    )

    result = classify_emotion(features)

    assert result.label == "neutral"


def test_every_result_carries_the_standard_disclaimer() -> None:
    features = ProsodyFeatures(
        pitch_mean_hz=165.0, pitch_std_hz=18.0, energy_mean=0.03, energy_std=0.004, voiced_ratio=0.5
    )

    result = classify_emotion(features)

    assert result.disclaimer == "Estimated from voice tone, not verified."


def test_confidence_is_always_within_bounds() -> None:
    for pitch_std in (0.0, 10.0, 50.0, 200.0):
        features = ProsodyFeatures(
            pitch_mean_hz=165.0, pitch_std_hz=pitch_std, energy_mean=0.1, energy_std=0.05, voiced_ratio=0.6
        )
        result = classify_emotion(features)
        assert 0.0 <= result.confidence <= 1.0
