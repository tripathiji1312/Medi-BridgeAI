"""Real ASR provider: faster-whisper (CTranslate2 Whisper), chosen for Phase 1
per the decision recorded in docs/PROGRESS.md -- local/self-hosted so no
third-party retains patient audio (Blueprint Section 6.1 hard constraint).

Import of faster_whisper/numpy is deferred into __init__ so importing this
module (and app.main, which wires providers) never requires the heavy
dependency to be installed -- tests run against FixtureASRProvider instead.
"""

from __future__ import annotations

import math

from app.asr.provider import ASRProvider
from app.asr.schemas import TranscriptSegment

EXPECTED_SAMPLE_RATE = 16_000


class FasterWhisperASRProvider(ASRProvider):
    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "hi",
    ) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:  # pragma: no cover - exercised only when the
            # optional heavy dependency isn't installed.
            raise RuntimeError(
                "faster-whisper is not installed. Install "
                "services/speech-pipeline/requirements-asr.txt to use the real "
                "ASR provider; otherwise use FixtureASRProvider for tests."
            ) from exc

        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self._language = language

    def transcribe(self, pcm16_mono: bytes, sample_rate: int) -> list[TranscriptSegment]:
        if sample_rate != EXPECTED_SAMPLE_RATE:
            raise ValueError(
                f"FasterWhisperASRProvider expects {EXPECTED_SAMPLE_RATE}Hz audio, "
                f"got {sample_rate}Hz. Resample before calling transcribe()."
            )

        import numpy as np

        audio = np.frombuffer(pcm16_mono, dtype="<i2").astype(np.float32) / 32768.0
        segments, info = self._model.transcribe(
            audio,
            language=self._language,
            vad_filter=True,
            word_timestamps=False,
        )

        results: list[TranscriptSegment] = []
        for seg in segments:
            # avg_logprob is a log-probability (<= 0); map to a 0-1 confidence
            # rather than fabricating a number -- Blueprint Section 11.1 "no
            # numeric fabrication."
            confidence = math.exp(seg.avg_logprob) if seg.avg_logprob is not None else 0.0
            results.append(
                TranscriptSegment(
                    text=seg.text.strip(),
                    is_final=True,
                    confidence=min(max(confidence, 0.0), 1.0),
                    start_ms=int(seg.start * 1000),
                    end_ms=int(seg.end * 1000),
                    language=info.language or self._language,
                )
            )
        return results
