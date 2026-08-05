"""Integration test: WebSocket client streams the pre-recorded fixture in
chunks and receives partial/final transcript events -- the Phase 1
end-to-end contract (Blueprint Section 3.2 steps 1-3, 9)."""

from __future__ import annotations

import wave
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.transcribe_ws import create_transcribe_router
from tests.stub_provider import (
    RecordingStubASRProvider,
    RecordingStubEmbeddingProvider,
    RecordingStubEmergencyDetector,
    RecordingStubEmotionClassifier,
    RecordingStubEntityExtractor,
    RecordingStubMiscommunicationChecker,
    RecordingStubMTProvider,
    RecordingStubOrchestratorClient,
    RecordingStubRiskScorer,
    RecordingStubTTSProvider,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_utterance.wav"
CHUNK_BYTES = 3200  # ~100ms at 16kHz/16-bit mono; simulates realistic client chunking


def _load_fixture() -> bytes:
    with wave.open(str(FIXTURE_PATH), "rb") as wf:
        return wf.readframes(wf.getnframes())


def _build_app(
    provider: RecordingStubASRProvider,
    mt_provider: RecordingStubMTProvider | None = None,
    tts_provider: RecordingStubTTSProvider | None = None,
    get_embedding_provider: Any = None,
    misco_checker: RecordingStubMiscommunicationChecker | None = None,
    orchestrator_client: RecordingStubOrchestratorClient | None = None,
    entity_extractor: RecordingStubEntityExtractor | None = None,
    emergency_detector: RecordingStubEmergencyDetector | None = None,
    emotion_classifier: RecordingStubEmotionClassifier | None = None,
    risk_scorer: RecordingStubRiskScorer | None = None,
) -> FastAPI:
    app = FastAPI()
    app.include_router(
        create_transcribe_router(
            lambda: provider,
            (lambda: mt_provider) if mt_provider is not None else None,
            (lambda: tts_provider) if tts_provider is not None else None,
            get_embedding_provider,
            (lambda: misco_checker) if misco_checker is not None else None,
            (lambda: orchestrator_client) if orchestrator_client is not None else None,
            (lambda: entity_extractor) if entity_extractor is not None else None,
            (lambda: emergency_detector) if emergency_detector is not None else None,
            (lambda: emotion_classifier) if emotion_classifier is not None else None,
            (lambda: risk_scorer) if risk_scorer is not None else None,
        )
    )
    return app


def test_websocket_streams_final_transcript_events_for_the_fixture() -> None:
    provider = RecordingStubASRProvider(text="fixture transcript")
    app = _build_app(provider)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])

            events = []
            finals = []
            # The fixture contains two utterances separated by >500ms of
            # silence, so at least two "final" events must arrive; keep
            # reading (partials may interleave) until we have both, with a
            # bound so a regression fails the test instead of hanging.
            for _ in range(50):
                event = ws.receive_json()
                events.append(event)
                if event["type"] == "final":
                    finals.append(event)
                if len(finals) >= 2:
                    break

    assert len(finals) >= 2, f"only received {len(finals)} final event(s): {events}"
    for event in finals:
        assert event["segment"]["text"] == "fixture transcript"
        assert event["segment"]["is_final"] is True
        assert event["latency_ms"] is not None
        assert 0.0 <= event["segment"]["confidence"] <= 1.0
    # Every event carries the same session_id (Blueprint Section 2.2: the
    # client needs this to query orchestrator's conversation memory), and
    # it's a real generated id, not the "n/a" placeholder.
    session_ids = {event["session_id"] for event in events}
    assert len(session_ids) == 1
    assert next(iter(session_ids)) != "n/a"


def test_websocket_reports_error_and_closes_when_provider_is_unavailable() -> None:
    def unavailable_provider() -> RecordingStubASRProvider:
        raise RuntimeError("ASR model not installed")

    app = FastAPI()
    app.include_router(create_transcribe_router(unavailable_provider))

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            message = ws.receive_json()
            assert message["type"] == "error"
            assert "not installed" in message["error"]


def _finals_from(ws) -> list[dict[str, Any]]:  # type: ignore[no-untyped-def]
    finals: list[dict[str, Any]] = []
    for _ in range(50):
        event = ws.receive_json()
        if event["type"] == "final":
            finals.append(event)
        if len(finals) >= 2:
            break
    return finals


def test_final_events_carry_translation_and_tts_audio_when_both_providers_succeed() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    mt_provider = RecordingStubMTProvider(translated_text="fixture translation")
    tts_provider = RecordingStubTTSProvider(audio=b"\x11\x22\x33\x44")
    app = _build_app(asr_provider, mt_provider, tts_provider)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["translation"]["text"] == "fixture translation"
        assert event["translation"]["target_language"] == "en"
        assert event["translation_error"] is None
        assert event["back_translation"]["text"] == "fixture translation"  # stub echoes translated_text
        assert event["back_translation_error"] is None
        assert event["tts"]["sample_rate"] == 16_000
        assert event["tts"]["format"] == "pcm16"
        assert event["tts_error"] is None
    # MT runs twice per final (forward HI->EN, then back EN->HI), never on
    # partials -- translating unstable text would waste compute and flicker
    # on screen.
    assert mt_provider.calls == [
        "fixture transcript",
        "fixture translation",
        "fixture transcript",
        "fixture translation",
    ]


def test_translation_failure_still_delivers_the_raw_transcript_degraded_not_dropped() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    mt_provider = RecordingStubMTProvider(should_fail=True)
    tts_provider = RecordingStubTTSProvider()
    app = _build_app(asr_provider, mt_provider, tts_provider)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["segment"]["text"] == "fixture transcript"  # raw transcript still present
        assert event["translation"] is None
        assert "unavailable" in event["translation_error"]
        assert event["tts"] is None  # TTS never runs without a translation to speak
    assert tts_provider.calls == []


def test_tts_failure_still_delivers_transcript_and_translation_degraded_not_dropped() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    mt_provider = RecordingStubMTProvider(translated_text="fixture translation")
    tts_provider = RecordingStubTTSProvider(should_fail=True)
    app = _build_app(asr_provider, mt_provider, tts_provider)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["translation"]["text"] == "fixture translation"
        assert event["tts"] is None
        assert "unavailable" in event["tts_error"]


def test_final_events_carry_a_speaker_assignment_when_diarization_succeeds() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    embedding_provider = RecordingStubEmbeddingProvider()
    app = _build_app(asr_provider, get_embedding_provider=lambda: embedding_provider)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["speaker"]["speaker_label"] in ("speaker_a", "speaker_b")
        assert 0.0 <= event["speaker"]["confidence"] <= 1.0
        assert event["speaker_error"] is None
    # Diarization only runs on finals, same rule as MT/TTS.
    assert len(embedding_provider.calls) == len(finals)


def test_diarization_embedding_failure_still_delivers_transcript_degraded_not_dropped() -> None:
    class FailingEmbeddingProvider:
        def embed(self, pcm16_mono: bytes, sample_rate: int) -> list[float]:
            raise RuntimeError("embedding extraction failed")

    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    app = _build_app(asr_provider, get_embedding_provider=lambda: FailingEmbeddingProvider())
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["segment"]["text"] == "fixture transcript"  # raw transcript still present
        assert event["speaker"] is None
        assert "extraction failed" in event["speaker_error"]


def test_diarization_model_unavailable_at_connection_time_degrades_the_whole_session() -> None:
    def unavailable_embedding_provider():  # type: ignore[no-untyped-def]
        raise RuntimeError("speechbrain not installed")

    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    app = _build_app(asr_provider, get_embedding_provider=unavailable_embedding_provider)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["segment"]["text"] == "fixture transcript"
        assert event["speaker"] is None
        assert "not installed" in event["speaker_error"]


def test_final_events_carry_a_miscommunication_result_and_confidence_v2_when_the_check_succeeds() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript", confidence=0.8)
    mt_provider = RecordingStubMTProvider(translated_text="fixture translation")
    misco_checker = RecordingStubMiscommunicationChecker(
        consistent=True, similarity_score=0.9, reason="matches closely"
    )
    app = _build_app(asr_provider, mt_provider, misco_checker=misco_checker)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["miscommunication"]["consistent"] is True
        assert event["miscommunication"]["similarity_score"] == 0.9
        assert event["miscommunication_error"] is None
        # composite = 0.8 * 0.5 + 0.9 * 0.5 = 0.85 -> green band per Blueprint thresholds
        assert event["confidence_v2"] == pytest.approx(0.85)
        assert event["confidence_band"] == "green"
    # The checker receives the original transcript and the (stubbed) back
    # translation, not the forward translation.
    assert misco_checker.calls == [("fixture transcript", "fixture translation")] * 2


def test_miscommunication_check_failure_still_delivers_translation_degraded_not_dropped() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    mt_provider = RecordingStubMTProvider(translated_text="fixture translation")
    misco_checker = RecordingStubMiscommunicationChecker(should_fail=True)
    app = _build_app(asr_provider, mt_provider, misco_checker=misco_checker)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["translation"]["text"] == "fixture translation"  # earlier stage still present
        assert event["miscommunication"] is None
        assert "unavailable" in event["miscommunication_error"]
        # No partial/fabricated composite score when a signal is missing.
        assert event["confidence_v2"] is None
        assert event["confidence_band"] is None


def test_back_translation_failure_skips_miscommunication_check_but_keeps_forward_translation() -> None:
    class ForwardOnlyMTProvider:
        """Succeeds on HI->EN, fails on the EN->HI back leg."""

        def translate(self, text: str, source_lang: str, target_lang: str) -> object:
            from app.mt.schemas import TranslationSegment

            if target_lang == "hi":
                raise RuntimeError("back-translation unavailable")
            return TranslationSegment(text="fixture translation", source_language=source_lang, target_language=target_lang)

    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    misco_checker = RecordingStubMiscommunicationChecker()
    app = _build_app(asr_provider, ForwardOnlyMTProvider(), misco_checker=misco_checker)  # type: ignore[arg-type]
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["translation"]["text"] == "fixture translation"
        assert event["back_translation"] is None
        assert "unavailable" in event["back_translation_error"]
        assert event["miscommunication"] is None
        assert event["miscommunication_error"] is None  # never even attempted, not a failure of its own
    assert misco_checker.calls == []


def test_finalized_utterances_are_recorded_in_orchestrator_with_a_consistent_session_id() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    mt_provider = RecordingStubMTProvider(translated_text="fixture translation")
    orchestrator_client = RecordingStubOrchestratorClient()
    app = _build_app(asr_provider, mt_provider, orchestrator_client=orchestrator_client)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            _finals_from(ws)

    assert len(orchestrator_client.calls) == 2
    session_ids = {call[0] for call in orchestrator_client.calls}
    assert len(session_ids) == 1  # same WS connection -> same session_id throughout
    for _session_id, _speaker, original_text, translated_text in orchestrator_client.calls:
        assert original_text == "fixture transcript"
        assert translated_text == "fixture translation"


def test_orchestrator_recording_failure_does_not_crash_the_connection_or_drop_the_delivered_event() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    orchestrator_client = RecordingStubOrchestratorClient(should_fail=True)
    app = _build_app(asr_provider, orchestrator_client=orchestrator_client)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            # The connection must survive the recording failure and keep
            # delivering both finals, not drop the second one or hang.
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["segment"]["text"] == "fixture transcript"


def test_final_events_carry_entities_extracted_from_both_hindi_and_english_text() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    mt_provider = RecordingStubMTProvider(translated_text="fixture translation")
    entity_extractor = RecordingStubEntityExtractor()
    app = _build_app(asr_provider, mt_provider, entity_extractor=entity_extractor)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["entities"][0]["canonical_name"] == "stub symptom"
        assert event["entities_error"] is None
        assert event["translation_entities"][0]["canonical_name"] == "stub symptom"
        assert event["translation_entities_error"] is None
    # Extraction runs once for the Hindi text, once for the English
    # translation, per final event.
    assert entity_extractor.calls == [
        ("fixture transcript", "hi"),
        ("fixture translation", "en"),
    ] * 2


def test_entity_extraction_failure_on_hindi_side_does_not_block_translation_side() -> None:
    class HindiFailsEntityExtractor:
        """Fails for Hindi text, succeeds for English."""

        async def extract(self, text: str, language: str) -> list[object]:
            if language == "hi":
                raise RuntimeError("clinical-nlp unavailable")
            from app.clinical_nlp.schemas import MedicalEntity

            return [
                MedicalEntity(
                    text="fever",
                    category="symptom",
                    canonical_name="fever",
                    canonical_code="R50.9",
                    definition="elevated body temperature",
                    confidence=1.0,
                    start_char=0,
                    end_char=5,
                    is_fuzzy_match=False,
                )
            ]

    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    mt_provider = RecordingStubMTProvider(translated_text="fixture translation")
    app = _build_app(
        asr_provider, mt_provider, entity_extractor=HindiFailsEntityExtractor()  # type: ignore[arg-type]
    )
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["segment"]["text"] == "fixture transcript"  # earlier stages still present
        assert event["entities"] is None
        assert "unavailable" in event["entities_error"]
        assert event["translation_entities"][0]["canonical_name"] == "fever"
        assert event["translation_entities_error"] is None


def test_entity_extraction_only_runs_on_finals_not_partials() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    entity_extractor = RecordingStubEntityExtractor()
    app = _build_app(asr_provider, entity_extractor=entity_extractor)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            _finals_from(ws)

    # No MT provider here, so only the Hindi-side extraction runs (no
    # translation to extract from) -- one call per final, none per partial.
    assert entity_extractor.calls == [("fixture transcript", "hi")] * 2


def test_final_events_carry_an_emergency_result_when_the_check_succeeds() -> None:
    asr_provider = RecordingStubASRProvider(text="chest pain")
    emergency_detector = RecordingStubEmergencyDetector(alert=True, reason="Detected emergency keyword(s): chest pain.")
    app = _build_app(asr_provider, emergency_detector=emergency_detector)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["emergency"]["alert"] is True
        assert "chest pain" in event["emergency"]["reason"]
        assert event["emergency_error"] is None
    assert emergency_detector.calls == [("chest pain", "hi")] * 2


def test_emergency_detection_failure_still_delivers_transcript_degraded_not_dropped() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    emergency_detector = RecordingStubEmergencyDetector(should_fail=True)
    app = _build_app(asr_provider, emergency_detector=emergency_detector)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["segment"]["text"] == "fixture transcript"
        assert event["emergency"] is None
        assert "unavailable" in event["emergency_error"]


def test_emergency_detection_runs_on_the_hindi_original_regardless_of_translation() -> None:
    # Blueprint Section 3.2 step 10: emergency detection must not wait on
    # (or depend on) translation succeeding -- proven here by it running
    # correctly with no MT provider configured at all.
    asr_provider = RecordingStubASRProvider(text="chest pain")
    emergency_detector = RecordingStubEmergencyDetector(alert=True, reason="Detected emergency keyword(s): chest pain.")
    app = _build_app(asr_provider, emergency_detector=emergency_detector)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    assert finals[0]["emergency"]["alert"] is True


def test_final_events_carry_an_emotion_assessment_when_classification_succeeds() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    emotion_classifier = RecordingStubEmotionClassifier(label="anxious", confidence=0.7, reason="stub reason")
    app = _build_app(asr_provider, emotion_classifier=emotion_classifier)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["emotion"]["label"] == "anxious"
        assert event["emotion"]["confidence"] == 0.7
        assert event["emotion"]["disclaimer"] == "Estimated from voice tone, not verified."
        assert event["emotion_error"] is None
    assert len(emotion_classifier.calls) == 2


def test_emotion_classification_failure_still_delivers_transcript_degraded_not_dropped() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    emotion_classifier = RecordingStubEmotionClassifier(should_fail=True)
    app = _build_app(asr_provider, emotion_classifier=emotion_classifier)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["segment"]["text"] == "fixture transcript"
        assert event["emotion"] is None
        assert "unavailable" in event["emotion_error"]


def test_emotion_classification_only_runs_on_finals_not_partials() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    emotion_classifier = RecordingStubEmotionClassifier()
    app = _build_app(asr_provider, emotion_classifier=emotion_classifier)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            _finals_from(ws)

    assert len(emotion_classifier.calls) == 2


def test_final_events_carry_a_risk_assessment_and_pass_the_emotion_signal_through() -> None:
    asr_provider = RecordingStubASRProvider(text="I have chest pain")
    emotion_classifier = RecordingStubEmotionClassifier(label="fearful", confidence=0.8, reason="stub reason")
    risk_scorer = RecordingStubRiskScorer(level="high", raw_level="high", reason="stub reason", emergency_triggered=True)
    app = _build_app(asr_provider, emotion_classifier=emotion_classifier, risk_scorer=risk_scorer)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["risk"]["level"] == "high"
        assert event["risk_error"] is None
    # Risk scoring receives the emotion signal computed earlier in the same
    # chain, not a bare text -- proves the cross-stage composition works.
    for call in risk_scorer.calls:
        assert call[2] == "fearful"
        assert call[3] == 0.8


def test_risk_scoring_failure_still_delivers_transcript_degraded_not_dropped() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    risk_scorer = RecordingStubRiskScorer(should_fail=True)
    app = _build_app(asr_provider, risk_scorer=risk_scorer)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            finals = _finals_from(ws)

    assert len(finals) >= 2
    for event in finals:
        assert event["segment"]["text"] == "fixture transcript"
        assert event["risk"] is None
        assert "unavailable" in event["risk_error"]


def test_risk_scoring_only_runs_on_finals_not_partials() -> None:
    asr_provider = RecordingStubASRProvider(text="fixture transcript")
    risk_scorer = RecordingStubRiskScorer()
    app = _build_app(asr_provider, risk_scorer=risk_scorer)
    audio = _load_fixture()

    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as ws:
            for i in range(0, len(audio), CHUNK_BYTES):
                ws.send_bytes(audio[i : i + CHUNK_BYTES])
            _finals_from(ws)

    assert len(risk_scorer.calls) == 2
