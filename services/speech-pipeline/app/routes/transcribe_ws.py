"""WebSocket transcript streaming endpoint (Blueprint Section 3.2 steps 1-7):
audio in -> Hindi transcript -> English translation + TTS audio -> speaker
label, all pushed back over the same connection.

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
from app.diarization.diarizer import SpeakerDiarizer
from app.diarization.provider import SpeakerEmbeddingProvider
from app.mt.provider import MTProvider
from app.tts.provider import TTSProvider

logger = logging.getLogger(__name__)

MTProviderGetter = Callable[[], MTProvider]
TTSProviderGetter = Callable[[], TTSProvider]
EmbeddingProviderGetter = Callable[[], SpeakerEmbeddingProvider]


def create_transcribe_router(
    get_provider: Callable[[], ASRProvider],
    get_mt_provider: MTProviderGetter | None = None,
    get_tts_provider: TTSProviderGetter | None = None,
    get_embedding_provider: EmbeddingProviderGetter | None = None,
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
        # One diarizer per connection: clustering state (who's "speaker_a"
        # vs "speaker_b") must not leak across sessions/patients. Built
        # eagerly (not lazily inside the enrichment call) so a persistently
        # broken embedding model degrades once per connection, not silently
        # retries on every utterance.
        diarizer: SpeakerDiarizer | None = None
        diarizer_error: str | None = None
        if get_embedding_provider is not None:
            try:
                diarizer = SpeakerDiarizer(get_embedding_provider())
            except Exception as exc:  # noqa: BLE001 - degrade, don't crash the session
                logger.exception("diarization unavailable for this session")
                diarizer_error = str(exc)

        try:
            while True:
                chunk = await websocket.receive_bytes()
                for event in session.push_chunk(chunk):
                    event = _enrich_final_event(
                        event, get_mt_provider, get_tts_provider, session, diarizer, diarizer_error
                    )
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
    session: StreamingASRSession,
    diarizer: SpeakerDiarizer | None,
    diarizer_error: str | None,
) -> TranscriptEvent:
    """Runs MT, then TTS, then diarization on a finalized ASR event. Partials
    are left alone -- translating/diarizing unstable text wastes compute and
    would flicker on screen.

    Each stage's failure is independent and never drops what earlier stages
    already computed: the client always has at least the raw Hindi text +
    ASR confidence even in fully degraded mode (Blueprint Section 7.2).
    """
    if event.type != "final" or event.segment is None or not event.segment.text.strip():
        return event

    event = _run_translation(event, get_mt_provider)
    event = _run_tts(event, get_tts_provider)
    event = _run_diarization(event, session, diarizer, diarizer_error)
    return event


def _run_translation(event: TranscriptEvent, get_mt_provider: MTProviderGetter | None) -> TranscriptEvent:
    if get_mt_provider is None:
        return event
    try:
        segment = event.segment
        assert segment is not None
        translation = get_mt_provider().translate(segment.text, segment.language, "en")
        return event.model_copy(update={"translation": translation})
    except Exception as exc:  # noqa: BLE001 - any MT failure degrades, never crashes the session
        logger.exception("translation failed for utterance %s", event.utterance_id)
        return event.model_copy(update={"translation_error": str(exc)})


def _run_tts(event: TranscriptEvent, get_tts_provider: TTSProviderGetter | None) -> TranscriptEvent:
    if get_tts_provider is None or event.translation is None:
        return event
    try:
        tts_segment = get_tts_provider().synthesize(event.translation.text, event.translation.target_language)
        return event.model_copy(update={"tts": tts_segment})
    except Exception as exc:  # noqa: BLE001 - same degrade-not-crash rule as above
        logger.exception("tts failed for utterance %s", event.utterance_id)
        return event.model_copy(update={"tts_error": str(exc)})


def _run_diarization(
    event: TranscriptEvent,
    session: StreamingASRSession,
    diarizer: SpeakerDiarizer | None,
    diarizer_error: str | None,
) -> TranscriptEvent:
    if diarizer is None:
        if diarizer_error is not None:
            return event.model_copy(update={"speaker_error": diarizer_error})
        return event

    audio = session.get_utterance_audio(event.utterance_id)
    if audio is None:
        return event.model_copy(update={"speaker_error": "utterance audio unavailable for diarization"})

    try:
        assignment = diarizer.assign_speaker(audio, session.sample_rate)
        return event.model_copy(update={"speaker": assignment})
    except Exception as exc:  # noqa: BLE001 - same degrade-not-crash rule as above
        logger.exception("diarization failed for utterance %s", event.utterance_id)
        return event.model_copy(update={"speaker_error": str(exc)})
