"""Deterministic, documented threshold classifier over real prosodic
features (Blueprint Section 4's "lightweight classifier head"). Rules are
ordered, first-match-wins, and each branch's reason string names the exact
features that triggered it -- every emotion label is explainable by
construction, not just labeled with a confidence number.

Known, explicitly documented limitation: prosody (pitch + energy) primarily
captures *arousal* (how activated/energetic speech sounds), not *valence*
(positive vs. negative). Happy and Angry can look acoustically similar
(both loud, both higher-pitched) -- there is no reliable way to tell them
apart from pitch/energy alone. The "happy" branch below has a lower
confidence ceiling than the others specifically because of this, and the
disclaimer shown alongside every result exists for exactly this reason.
None of these thresholds are tuned against a labeled gold set -- qualitative
starting points, same caveat as every other heuristic threshold in this
build (diarization clustering distance, miscommunication similarity,
fuzzy-match ratio).
"""

from __future__ import annotations

from app.emotion.features import ProsodyFeatures
from app.emotion.schemas import EmotionAssessment

REFERENCE_PITCH_HZ = 165.0  # broad population average across adult speech; no per-speaker baseline yet
HIGH_ENERGY_THRESHOLD = 0.08  # RMS on a [-1, 1] normalized signal
LOW_ENERGY_THRESHOLD = 0.02
MIN_VOICED_RATIO = 0.15
HIGH_VOICED_RATIO = 0.70
LOW_VARIABILITY_CV = 0.08


def _confidence(base: float, strength: float, cap: float = 0.9) -> float:
    return max(0.0, min(cap, base + strength * 0.3))


def classify_emotion(features: ProsodyFeatures) -> EmotionAssessment:
    if features.voiced_ratio < MIN_VOICED_RATIO:
        return EmotionAssessment(
            label="neutral",
            confidence=0.3,
            reason="Not enough voiced speech in this utterance to assess tone confidently.",
        )

    pitch_cv = features.pitch_std_hz / features.pitch_mean_hz if features.pitch_mean_hz > 0 else 0.0
    energy_cv = features.energy_std / features.energy_mean if features.energy_mean > 0 else 0.0
    pitch_ratio = features.pitch_mean_hz / REFERENCE_PITCH_HZ if features.pitch_mean_hz > 0 else 1.0

    if pitch_cv > 0.30 and features.energy_mean > HIGH_ENERGY_THRESHOLD:
        strength = (pitch_cv - 0.30) + (features.energy_mean - HIGH_ENERGY_THRESHOLD) * 5
        return EmotionAssessment(
            label="angry",
            confidence=_confidence(0.55, strength),
            reason=(
                f"Loud (RMS {features.energy_mean:.3f}) with highly variable pitch "
                f"(coefficient of variation {pitch_cv:.2f}) -- consistent with anger or agitation."
            ),
        )

    if pitch_ratio > 1.25 and features.energy_mean < LOW_ENERGY_THRESHOLD:
        strength = (pitch_ratio - 1.25) + (LOW_ENERGY_THRESHOLD - features.energy_mean) * 10
        return EmotionAssessment(
            label="fearful",
            confidence=_confidence(0.5, strength),
            reason=(
                f"Pitch well above typical ({features.pitch_mean_hz:.0f}Hz vs a "
                f"{REFERENCE_PITCH_HZ:.0f}Hz reference) with low volume -- consistent with fear."
            ),
        )

    if pitch_cv > 0.25 and features.voiced_ratio > HIGH_VOICED_RATIO:
        strength = (pitch_cv - 0.25) + (features.voiced_ratio - HIGH_VOICED_RATIO)
        return EmotionAssessment(
            label="anxious",
            confidence=_confidence(0.5, strength),
            reason=(
                f"Highly variable pitch (coefficient of variation {pitch_cv:.2f}) with little "
                f"pausing (voiced ratio {features.voiced_ratio:.2f}) -- consistent with anxiety."
            ),
        )

    if features.energy_mean > HIGH_ENERGY_THRESHOLD and pitch_ratio > 1.15:
        strength = (features.energy_mean - HIGH_ENERGY_THRESHOLD) * 5 + (pitch_ratio - 1.15)
        return EmotionAssessment(
            label="happy",
            confidence=_confidence(0.35, strength, cap=0.55),
            reason=(
                "Loud and higher-pitched than typical -- consistent with positive excitement, "
                "though this acoustic pattern can also indicate anger (prosody alone can't "
                "reliably distinguish positive from negative high-arousal states; see disclaimer)."
            ),
        )

    if pitch_cv > 0.18 or energy_cv > 0.18:
        strength = max(pitch_cv, energy_cv) - 0.18
        return EmotionAssessment(
            label="stressed",
            confidence=_confidence(0.45, strength),
            reason=(
                f"Elevated variability in pitch (CV {pitch_cv:.2f}) and/or loudness "
                f"(CV {energy_cv:.2f}) across the utterance -- consistent with stress."
            ),
        )

    if pitch_cv < LOW_VARIABILITY_CV and energy_cv < LOW_VARIABILITY_CV:
        strength = LOW_VARIABILITY_CV - max(pitch_cv, energy_cv)
        return EmotionAssessment(
            label="calm",
            confidence=_confidence(0.45, strength),
            reason=(
                f"Steady pitch (CV {pitch_cv:.2f}) and loudness (CV {energy_cv:.2f}) "
                "throughout -- consistent with a calm tone."
            ),
        )

    return EmotionAssessment(
        label="neutral",
        confidence=0.4,
        reason="No strong prosodic markers detected; tone appears typical.",
    )
