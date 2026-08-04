"""WebSocket transcript streaming endpoint (Blueprint Section 3.2 steps 1-9):
audio in -> Hindi transcript -> English translation -> back-translation +
miscommunication check + confidence v2 -> TTS audio -> speaker label, all
pushed back over the same connection.

Router is built via a factory so every provider is injectable -- tests pass
fixtures, app/main.py passes the real (lazy) providers. This keeps each
model swappable without touching routing/session logic
(AGENT_INSTRUCTIONS.md Section 3.1 abstraction rule).
"""

from __future__ import annotations

import logging
import uuid
from typing import Callable

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.asr.provider import ASRProvider
from app.asr.schemas import TranscriptEvent
from app.asr.session import StreamingASRSession
from app.clinical_nlp.provider import MiscommunicationChecker
from app.confidence.scoring import compute_confidence_v2, confidence_band
from app.diarization.diarizer import SpeakerDiarizer
from app.diarization.provider import SpeakerEmbeddingProvider
from app.mt.provider import MTProvider
from app.orchestrator_client import OrchestratorClient
from app.tts.provider import TTSProvider

logger = logging.getLogger(__name__)

MTProviderGetter = Callable[[], MTProvider]
TTSProviderGetter = Callable[[], TTSProvider]
EmbeddingProviderGetter = Callable[[], SpeakerEmbeddingProvider]
MiscommunicationCheckerGetter = Callable[[], MiscommunicationChecker]
OrchestratorClientGetter = Callable[[], OrchestratorClient]


def create_transcribe_router(
    get_provider: Callable[[], ASRProvider],
    get_mt_provider: MTProviderGetter | None = None,
    get_tts_provider: TTSProviderGetter | None = None,
    get_embedding_provider: EmbeddingProviderGetter | None = None,
    get_miscommunication_checker: MiscommunicationCheckerGetter | None = None,
    get_orchestrator_client: OrchestratorClientGetter | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.websocket("/ws/transcribe")
    async def transcribe_ws(websocket: WebSocket) -> None:
        await websocket.accept()

        # One conversation-memory session per connection (Blueprint Section
        # 2.2), sent on every event so the client can query orchestrator's
        # memory API. Not tied to any auth/patient identity yet -- Phase 9
        # (RBAC) is where a real session identity gets threaded through.
        session_id = uuid.uuid4().hex

        try:
            provider = get_provider()
        except RuntimeError as exc:
            # Fail loud, not silent (Blueprint Section 1 Principle 3): tell
            # the client ASR is unavailable instead of accepting audio that
            # will never produce a transcript.
            await websocket.send_json(
                TranscriptEvent(
                    type="error", utterance_id="n/a", session_id=session_id, error=str(exc)
                ).model_dump()
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
                    event = event.model_copy(update={"session_id": session_id})
                    event = await _enrich_final_event(
                        event,
                        get_mt_provider,
                        get_tts_provider,
                        get_miscommunication_checker,
                        session,
                        diarizer,
                        diarizer_error,
                    )
                    await websocket.send_json(event.model_dump())
                    await _record_utterance(event, session_id, get_orchestrator_client)
        except WebSocketDisconnect:
            for event in session.flush():
                # Nothing to send to a disconnected client; this exercises
                # the same finalize path so no in-progress utterance is
                # silently dropped, and gives orchestrator/audit a hook
                # point once that integration lands (Phase 4+).
                logger.info(
                    "session flushed on disconnect: utterance=%s type=%s",
                    event.utterance_id,
                    event.type,
                )

    return router


async def _enrich_final_event(
    event: TranscriptEvent,
    get_mt_provider: MTProviderGetter | None,
    get_tts_provider: TTSProviderGetter | None,
    get_miscommunication_checker: MiscommunicationCheckerGetter | None,
    session: StreamingASRSession,
    diarizer: SpeakerDiarizer | None,
    diarizer_error: str | None,
) -> TranscriptEvent:
    """Runs MT, back-translation + miscommunication check + confidence v2,
    TTS, then diarization on a finalized ASR event. Partials are left alone
    -- translating/diarizing unstable text wastes compute and would flicker
    on screen.

    Each stage's failure is independent and never drops what earlier stages
    already computed: the client always has at least the raw Hindi text +
    ASR confidence even in fully degraded mode (Blueprint Section 7.2).
    """
    if event.type != "final" or event.segment is None or not event.segment.text.strip():
        return event

    event = _run_translation(event, get_mt_provider)
    event = _run_back_translation(event, get_mt_provider)
    event = await _run_miscommunication_check(event, get_miscommunication_checker)
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


def _run_back_translation(event: TranscriptEvent, get_mt_provider: MTProviderGetter | None) -> TranscriptEvent:
    """EN -> HI, the reverse leg of Blueprint Section 3.2 step 6's
    back-translation consistency check. Only runs when the forward
    translation succeeded -- there's nothing to translate back otherwise."""
    if get_mt_provider is None or event.translation is None:
        return event
    try:
        back_translation = get_mt_provider().translate(
            event.translation.text, event.translation.target_language, event.translation.source_language
        )
        return event.model_copy(update={"back_translation": back_translation})
    except Exception as exc:  # noqa: BLE001 - same degrade-not-crash rule as above
        logger.exception("back-translation failed for utterance %s", event.utterance_id)
        return event.model_copy(update={"back_translation_error": str(exc)})


async def _run_miscommunication_check(
    event: TranscriptEvent, get_miscommunication_checker: MiscommunicationCheckerGetter | None
) -> TranscriptEvent:
    """Calls clinical-nlp (Blueprint Section 3.2 step 6) to compare the
    original Hindi against its back-translation, then folds the result's
    similarity score into confidence v2. Both fields are set together --
    a composite score without its underlying signals would be a fabricated
    number (Blueprint Section 11.1: no numeric fabrication), so
    confidence_v2/confidence_band stay None if the check didn't run.
    """
    if get_miscommunication_checker is None or event.back_translation is None:
        return event
    segment = event.segment
    assert segment is not None

    try:
        result = await get_miscommunication_checker().check(
            segment.text, event.back_translation.text, segment.language
        )
    except Exception as exc:  # noqa: BLE001 - same degrade-not-crash rule as above
        logger.exception("miscommunication check failed for utterance %s", event.utterance_id)
        return event.model_copy(update={"miscommunication_error": str(exc)})

    composite = compute_confidence_v2(segment.confidence, result.similarity_score)
    return event.model_copy(
        update={
            "miscommunication": result,
            "confidence_v2": composite,
            "confidence_band": confidence_band(composite),
        }
    )


def _run_tts(event: TranscriptEvent, get_tts_provider: TTSProviderGetter | None) -> TranscriptEvent:
    if get_tts_provider is None or event.translation is None:
        return event
    try:
        tts_segment = get_tts_provider().synthesize(event.translation.text, event.translation.target_language)
        return event.model_copy(update={"tts": tts_segment})
    except Exception as exc:  # noqa: BLE001 - same degrade-not-crash rule as above
        logger.exception("tts failed for utterance %s", event.utterance_id)
        return event.model_copy(update={"tts_error": str(exc)})


async def _record_utterance(
    event: TranscriptEvent, session_id: str, get_orchestrator_client: OrchestratorClientGetter | None
) -> None:
    """Best-effort: posts finalized utterances to orchestrator's
    conversation memory. Deliberately not folded into _enrich_final_event
    -- its outcome is never attached to the event sent to the client (see
    app.orchestrator_client's docstring for why), so it belongs after the
    client has already received its event, not in the enrichment chain
    that builds that event.

    Wrapped in its own try/except (unlike the real OrchestratorClient,
    which only swallows httpx errors) so that no matter what a given
    implementation does or doesn't catch internally, a memory-recording
    failure can never take down a connection that already delivered its
    event to the client.
    """
    if get_orchestrator_client is None or event.type != "final" or event.segment is None:
        return
    speaker = event.speaker.speaker_label if event.speaker else None
    translated_text = event.translation.text if event.translation else None
    try:
        await get_orchestrator_client().post_utterance(session_id, speaker, event.segment.text, translated_text)
    except Exception:  # noqa: BLE001 - best-effort side effect, must never crash the session
        logger.exception("failed to record utterance %s in orchestrator", event.utterance_id)


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
