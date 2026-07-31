"""WebSocket transcript streaming endpoint (Blueprint Section 3.2 steps 1-3,
Phase 1 scope: audio in -> raw Hindi transcript out, partial then final).

Router is built via a factory so the provider is injectable -- tests pass a
FixtureASRProvider, app/main.py passes the real (lazy) FasterWhisperASRProvider.
This keeps the ASR model swappable without touching this routing/session logic
(AGENT_INSTRUCTIONS.md Section 3.1 abstraction rule).
"""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.asr.provider import ASRProvider
from app.asr.schemas import TranscriptEvent
from app.asr.session import StreamingASRSession

logger = logging.getLogger(__name__)


def create_transcribe_router(get_provider: Callable[[], ASRProvider]) -> APIRouter:
    router = APIRouter()

    @router.websocket("/ws/transcribe")
    async def transcribe_ws(websocket: WebSocket) -> None:
        await websocket.accept()

        try:
            provider = get_provider()
        except RuntimeError as exc:
            # Fail loud, not silent (Blueprint Section 1 Principle 3): tell
            # the client ASR is unavailable instead of accepting audio that
            # will never produce a transcript.
            await websocket.send_json(
                TranscriptEvent(type="error", utterance_id="n/a", error=str(exc)).model_dump()
            )
            await websocket.close(code=1011)
            return

        session = StreamingASRSession(provider)

        try:
            while True:
                chunk = await websocket.receive_bytes()
                for event in session.push_chunk(chunk):
                    await websocket.send_json(event.model_dump())
        except WebSocketDisconnect:
            for event in session.flush():
                # Nothing to send to a disconnected client; this exercises
                # the same finalize path so no in-progress utterance is
                # silently dropped, and gives orchestrator/audit a hook
                # point once that integration lands (Phase 3+).
                logger.info(
                    "session flushed on disconnect: utterance=%s type=%s",
                    event.utterance_id,
                    event.type,
                )

    return router
