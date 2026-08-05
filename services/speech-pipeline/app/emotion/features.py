"""Real acoustic feature extraction from raw PCM16 mono audio -- pitch (F0)
via a simplified autocorrelation pitch tracker, RMS energy, and voiced-frame
ratio, computed per short frame and aggregated over the utterance. This is
genuine signal processing on the actual audio (same buffer diarization
already uses via StreamingASRSession.get_utterance_audio), not a fabricated
or hardcoded value -- see app.emotion.provider's docstring for why this
approach (vs. a pretrained end-to-end model) was chosen.

Not a full YIN/CREPE-grade pitch tracker -- the autocorrelation method here
is a standard, well-documented DSP technique but a simplified one. Good
enough to distinguish "high and variable" from "low and steady" pitch
patterns, which is all the rule-based classifier in rules.py needs; treat
per-frame F0 values as approximate, not lab-grade.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

FRAME_MS = 25
HOP_MS = 10
MIN_PITCH_HZ = 80
MAX_PITCH_HZ = 400
# Normalized autocorrelation peak strength below which a frame is judged
# unvoiced (silence/noise/consonant) rather than a genuine pitch period.
# Standard-order-of-magnitude threshold for this technique, not tuned
# against a labeled gold set -- same caveat as every other threshold
# introduced this build.
VOICED_AUTOCORR_THRESHOLD = 0.3


@dataclass
class ProsodyFeatures:
    pitch_mean_hz: float
    pitch_std_hz: float
    energy_mean: float
    energy_std: float
    voiced_ratio: float


def extract_prosody_features(pcm16_mono: bytes, sample_rate: int) -> ProsodyFeatures:
    samples = np.frombuffer(pcm16_mono, dtype=np.int16).astype(np.float64) / 32768.0
    frame_size = max(1, int(sample_rate * FRAME_MS / 1000))
    hop_size = max(1, int(sample_rate * HOP_MS / 1000))

    pitches: list[float] = []
    energies: list[float] = []
    voiced_flags: list[bool] = []

    last_start = len(samples) - frame_size
    for start in range(0, max(0, last_start) + 1, hop_size):
        frame = samples[start : start + frame_size]
        if len(frame) < frame_size:
            break
        energies.append(float(np.sqrt(np.mean(frame**2))))
        f0, voiced = _estimate_pitch(frame, sample_rate)
        voiced_flags.append(voiced)
        if voiced and f0 is not None:
            pitches.append(f0)

    if not energies:
        # Utterance shorter than one frame -- degrade to a single
        # whole-buffer energy estimate rather than raising.
        energy = float(np.sqrt(np.mean(samples**2))) if len(samples) else 0.0
        return ProsodyFeatures(0.0, 0.0, energy, 0.0, 0.0)

    voiced_ratio = sum(voiced_flags) / len(voiced_flags)
    pitch_mean = float(np.mean(pitches)) if pitches else 0.0
    pitch_std = float(np.std(pitches)) if len(pitches) > 1 else 0.0
    energy_mean = float(np.mean(energies))
    energy_std = float(np.std(energies))

    return ProsodyFeatures(pitch_mean, pitch_std, energy_mean, energy_std, voiced_ratio)


def _estimate_pitch(frame: np.ndarray, sample_rate: int) -> tuple[float | None, bool]:
    windowed = frame * np.hamming(len(frame))
    autocorr = np.correlate(windowed, windowed, mode="full")
    autocorr = autocorr[len(autocorr) // 2 :]
    if autocorr[0] <= 1e-9:
        return None, False

    min_lag = int(sample_rate / MAX_PITCH_HZ)
    max_lag = min(int(sample_rate / MIN_PITCH_HZ), len(autocorr) - 1)
    if max_lag <= min_lag:
        return None, False

    search = autocorr[min_lag : max_lag + 1]
    peak_index = int(np.argmax(search))
    peak_value = search[peak_index]
    normalized_strength = peak_value / autocorr[0]

    if normalized_strength < VOICED_AUTOCORR_THRESHOLD:
        return None, False

    lag = min_lag + peak_index
    if lag <= 0:
        return None, False
    return float(sample_rate / lag), True
