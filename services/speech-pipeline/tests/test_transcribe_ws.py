"""Integration test: WebSocket client streams the pre-recorded fixture in
chunks and receives partial/final transcript events -- the Phase 1
end-to-end contract (Blueprint Section 3.2 steps 1-3, 9)."""

from __future__ import annotations

import wave
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.transcribe_ws import create_transcribe_router
from tests.stub_provider import RecordingStubASRProvider

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_utterance.wav"
CHUNK_BYTES = 3200  # ~100ms at 16kHz/16-bit mono; simulates realistic client chunking


def _load_fixture() -> bytes:
    with wave.open(str(FIXTURE_PATH), "rb") as wf:
        return wf.readframes(wf.getnframes())


def _build_app(provider: RecordingStubASRProvider) -> FastAPI:
    app = FastAPI()
    app.include_router(create_transcribe_router(lambda: provider))
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
