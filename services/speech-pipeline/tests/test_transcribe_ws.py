"""Integration test: WebSocket client streams the pre-recorded fixture in
chunks and receives partial/final transcript events -- the Phase 1
end-to-end contract (Blueprint Section 3.2 steps 1-3, 9)."""

from __future__ import annotations

import wave
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.transcribe_ws import create_transcribe_router
from tests.stub_provider import (
    RecordingStubASRProvider,
    RecordingStubMTProvider,
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
) -> FastAPI:
    app = FastAPI()
    app.include_router(
        create_transcribe_router(
            lambda: provider,
            (lambda: mt_provider) if mt_provider is not None else None,
            (lambda: tts_provider) if tts_provider is not None else None,
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
        assert event["tts"]["sample_rate"] == 16_000
        assert event["tts"]["format"] == "pcm16"
        assert event["tts_error"] is None
    # MT only runs on finals, never partials -- translating unstable text
    # would waste compute and flicker on screen.
    assert mt_provider.calls == ["fixture transcript", "fixture transcript"]


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
