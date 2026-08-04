"""Client for orchestrator's session-memory API (Blueprint Section 2.2).
Posting an utterance is a best-effort side effect of the speech pipeline,
not a pipeline stage the client observes: unlike translation/TTS/
diarization, its success or failure isn't an AI-derived value shown to the
user, so a failure here is logged, not attached to the TranscriptEvent
(Blueprint Section 3.3: the memory/clinical path may lag or degrade
without gating the speech exchange itself).

Protocol + implementation split, same pattern as every other cross-service
client in this build (app.clinical_nlp.provider, app.mt.provider, etc.) --
lets tests substitute a recording stub without satisfying an unnecessarily
concrete type.
"""

from __future__ import annotations

import logging
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)


class OrchestratorClient(Protocol):
    async def post_utterance(
        self, session_id: str, speaker: str | None, original_text: str, translated_text: str | None
    ) -> None: ...


class HttpOrchestratorClient(OrchestratorClient):
    def __init__(self, base_url: str, timeout_seconds: float = 3.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def post_utterance(
        self, session_id: str, speaker: str | None, original_text: str, translated_text: str | None
    ) -> None:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            try:
                response = await client.post(
                    f"{self._base_url}/sessions/{session_id}/utterances",
                    json={
                        "speaker": speaker,
                        "original_text": original_text,
                        "translated_text": translated_text,
                    },
                )
                response.raise_for_status()
            except httpx.HTTPError:
                logger.exception("failed to record utterance in orchestrator (session=%s)", session_id)
