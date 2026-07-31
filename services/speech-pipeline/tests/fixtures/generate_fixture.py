"""Generates tests/fixtures/sample_utterance.wav.

SYNTHETIC fixture: two tone bursts (not real speech) separated by silence,
engineered to exercise VAD segmentation deterministically -- silence, then
~0.8s of tone (utterance 1), ~0.8s silence (well over the 500ms hang time
so utterance 1 finalizes), ~0.6s tone (utterance 2), trailing silence.

This is NOT a real Hindi speech sample. No network-sourced audio was used
(no vetted license/authenticity source available in this build environment)
and no offline Hindi TTS engine is installed. A real spoken-Hindi fixture
set is a follow-up task once one is sourced/recorded and reviewed -- logged
as a deferred item in docs/PROGRESS.md. This synthetic fixture is sufficient
for what Phase 1 targets: proving the pipeline (VAD segmentation,
partial/final event sequencing, latency instrumentation) works end-to-end
against a pre-recorded file before live mic input is wired up.

Run: python tests/fixtures/generate_fixture.py
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 16_000
OUT_PATH = Path(__file__).parent / "sample_utterance.wav"


def tone_burst(duration_s: float, freq_hz: float, amplitude: int = 8000) -> bytes:
    n = int(SAMPLE_RATE * duration_s)
    samples = [int(amplitude * math.sin(2 * math.pi * freq_hz * i / SAMPLE_RATE)) for i in range(n)]
    return struct.pack(f"<{n}h", *samples)


def silence(duration_s: float) -> bytes:
    n = int(SAMPLE_RATE * duration_s)
    return struct.pack(f"<{n}h", *([0] * n))


def build_fixture_audio() -> bytes:
    return (
        silence(0.3)
        + tone_burst(0.8, 220.0)  # "utterance 1"
        + silence(0.8)  # > SILENCE_HANG_MS, forces utterance 1 to finalize
        + tone_burst(0.6, 330.0)  # "utterance 2"
        + silence(0.8)  # > SILENCE_HANG_MS, forces utterance 2 to finalize too
    )


def main() -> None:
    audio = build_fixture_audio()
    with wave.open(str(OUT_PATH), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio)
    print(f"wrote {OUT_PATH} ({len(audio)} bytes, {len(audio) / 2 / SAMPLE_RATE:.2f}s)")


if __name__ == "__main__":
    main()
