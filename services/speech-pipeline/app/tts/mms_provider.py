"""Real TTS provider: facebook/mms-tts-eng via transformers (VITS), local/
self-hosted -- reuses the torch/transformers stack already required for
NLLB MT rather than adding a separate TTS dependency family.

Import of transformers/torch/numpy is deferred into __init__/synthesize, same
pattern as the ASR/MT real providers, so importing this module never requires
the heavy optional dependency to be installed.
"""

from __future__ import annotations

import base64

from app.tts.provider import TTSProvider
from app.tts.schemas import TTSAudioSegment


class MmsTTSProvider(TTSProvider):
    def __init__(self, model_name: str = "facebook/mms-tts-eng") -> None:
        try:
            from transformers import AutoTokenizer, VitsModel
        except ImportError as exc:  # pragma: no cover - exercised only when the
            # optional heavy dependency isn't installed.
            raise RuntimeError(
                "transformers/torch are not installed. Install "
                "services/speech-pipeline/requirements-mt.txt to use the real "
                "TTS provider; otherwise use FixtureTTSProvider for tests."
            ) from exc

        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = VitsModel.from_pretrained(model_name)
        self._sample_rate: int = self._model.config.sampling_rate

    def synthesize(self, text: str, language: str) -> TTSAudioSegment:
        import numpy as np
        import torch

        inputs = self._tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            output = self._model(**inputs).waveform

        waveform = output.squeeze().cpu().numpy()
        clamped = np.clip(waveform, -1.0, 1.0)
        pcm16 = (clamped * 32767).astype(np.int16).tobytes()

        return TTSAudioSegment(
            audio_base64=base64.b64encode(pcm16).decode("ascii"),
            sample_rate=self._sample_rate,
            format="pcm16",
        )
