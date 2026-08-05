"""Verifies app.emotion.features against synthetic signals with known
ground truth -- a pure sine wave at a known frequency should be detected as
voiced with a pitch estimate close to that frequency; silence should be
almost entirely unvoiced. This is what makes the real DSP path testable at
all without recorded human emotional speech (which this repo doesn't have).
"""

from __future__ import annotations

import numpy as np

from app.emotion.features import extract_prosody_features

SAMPLE_RATE = 16_000


def _sine_wave_pcm16(frequency_hz: float, duration_s: float, amplitude: float = 0.5) -> bytes:
    t = np.arange(int(SAMPLE_RATE * duration_s)) / SAMPLE_RATE
    samples = amplitude * np.sin(2 * np.pi * frequency_hz * t)
    return (samples * 32767).astype(np.int16).tobytes()


def _silence_pcm16(duration_s: float) -> bytes:
    return np.zeros(int(SAMPLE_RATE * duration_s), dtype=np.int16).tobytes()


def test_pure_tone_is_detected_as_voiced_with_pitch_close_to_its_frequency() -> None:
    audio = _sine_wave_pcm16(150.0, duration_s=1.0)

    features = extract_prosody_features(audio, SAMPLE_RATE)

    assert features.voiced_ratio > 0.9
    assert abs(features.pitch_mean_hz - 150.0) < 5.0
    # A single steady tone has ~zero pitch variability.
    assert features.pitch_std_hz < 2.0


def test_higher_pitch_tone_is_detected_correctly() -> None:
    audio = _sine_wave_pcm16(300.0, duration_s=1.0)

    features = extract_prosody_features(audio, SAMPLE_RATE)

    assert abs(features.pitch_mean_hz - 300.0) < 10.0


def test_silence_is_almost_entirely_unvoiced() -> None:
    audio = _silence_pcm16(duration_s=1.0)

    features = extract_prosody_features(audio, SAMPLE_RATE)

    assert features.voiced_ratio < 0.05
    assert features.energy_mean < 0.01


def test_louder_tone_has_higher_energy_than_a_quieter_one() -> None:
    quiet = extract_prosody_features(_sine_wave_pcm16(150.0, 1.0, amplitude=0.1), SAMPLE_RATE)
    loud = extract_prosody_features(_sine_wave_pcm16(150.0, 1.0, amplitude=0.8), SAMPLE_RATE)

    assert loud.energy_mean > quiet.energy_mean


def test_buffer_shorter_than_one_frame_degrades_instead_of_raising() -> None:
    tiny_audio = _sine_wave_pcm16(150.0, duration_s=0.001)  # ~16 samples at 16kHz

    features = extract_prosody_features(tiny_audio, SAMPLE_RATE)

    assert features.voiced_ratio == 0.0
    assert features.pitch_mean_hz == 0.0


def test_empty_buffer_does_not_raise() -> None:
    features = extract_prosody_features(b"", SAMPLE_RATE)

    assert features.voiced_ratio == 0.0
    assert features.energy_mean == 0.0
