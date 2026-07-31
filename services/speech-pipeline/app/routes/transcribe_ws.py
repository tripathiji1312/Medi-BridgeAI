"""WebSocket transcript streaming endpoint (Blueprint Section 3.2 steps 1-7):
audio in -> Hindi transcript -> (Phase 2) English translation + TTS audio,
all pushed back over the same connection.

Router is built via a factory so every provider is injectable -- tests pass
fixtures, app/main.py passes the real (lazy) providers. This keeps each
model swappable without touching routing/session logic
(AGENT_INSTRUCTIONS.md Section 3.1 abstraction rule).
"""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.asr.provider import ASRProvider
from app.asr.schemas import TranscriptEvent
from app.asr.session import StreamingASRSession
from app.mt.provider import MTProvider
from app.tts.provider import TTSProvider

logger = logging.getLogger(__name__)

MTProviderGetter = Callable[[], MTProvider]
TTSProviderGetter = Callable[[], TTSProvider]


def create_transcribe_router(
    get_provider: Callable[[], ASRProvider],
    get_mt_provider: MTProviderGetter | None = None,
    get_tts_provider: TTSProviderGetter | None = None,
) -> APIRouter:
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
                    event = _enrich_final_event(event, get_mt_provider, get_tts_provider)
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


def _enrich_final_event(
    event: TranscriptEvent,
    get_mt_provider: MTProviderGetter | None,
    get_tts_provider: TTSProviderGetter | None,
) -> TranscriptEvent:
    """Runs MT then TTS on a finalized ASR event. Partials are left alone --
    translating unstable text wastes compute and would flicker on screen.

    A translation/TTS failure never drops the underlying transcript: it's
    attached as *_error instead, so the client always has the raw Hindi
    text + ASR confidence even in degraded mode (Blueprint Section 7.2).
    """
    if event.type != "final" or event.segment is None or not event.segment.text.strip():
        return event
    if get_mt_provider is None:
        return event

    try:
        translation = get_mt_provider().translate(event.segment.text, event.segment.language, "en")
        event = event.model_copy(update={"translation": translation})
    except Exception as exc:  # noqa: BLE001 - any MT failure degrades, never crashes the session
        logger.exception("translation failed for utterance %s", event.utterance_id)
        return event.model_copy(update={"translation_error": str(exc)})

    if get_tts_provider is None:
        return event

    try:
        tts_segment = get_tts_provider().synthesize(translation.text, translation.target_language)
        event = event.model_copy(update={"tts": tts_segment})
    except Exception as exc:  # noqa: BLE001 - same degrade-not-crash rule as above
        logger.exception("tts failed for utterance %s", event.utterance_id)
        return event.model_copy(update={"tts_error": str(exc)})

    return event
