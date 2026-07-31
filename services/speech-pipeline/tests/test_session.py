"""Tests app.asr.session.StreamingASRSession against the synthetic
pre-recorded fixture (tests/fixtures/sample_utterance.wav), per Blueprint
Section 8 Phase 1: "Test with pre-recorded Hindi audio fixtures before live
mic. Latency instrumentation from day one."
"""

from __future__ import annotations

import wave
from pathlib import Path

from app.asr.session import StreamingASRSession
from tests.stub_provider import RecordingStubASRProvider

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_utterance.wav"


def _load_fixture() -> tuple[bytes, int]:
    with wave.open(str(FIXTURE_PATH), "rb") as wf:
        assert wf.getsampwidth() == 2
        assert wf.getnchannels() == 1
        audio = wf.readframes(wf.getnframes())
        return audio, wf.getframerate()


def test_streams_two_utterances_from_the_fixture_with_final_events() -> None:
    audio, sample_rate = _load_fixture()
    provider = RecordingStubASRProvider()
    session = StreamingASRSession(provider, sample_rate=sample_rate)

    events = session.push_chunk(audio)
    events += session.flush()

    finals = [e for e in events if e.type == "final"]
    assert len(finals) == 2, f"expected 2 finalized utterances, got {len(finals)}: {events}"

    for event in finals:
        assert event.segment is not None
        assert event.segment.is_final is True
        assert event.segment.text == "test transcript"
        assert event.latency_ms is not None and event.latency_ms >= 0
        # Every AI-derived value carries its "why" (confidence) --
        # AGENT_INSTRUCTIONS.md Rule 1.
        assert 0.0 <= event.segment.confidence <= 1.0


def test_finalized_utterances_have_distinct_ids_and_roughly_expected_duration() -> None:
    audio, sample_rate = _load_fixture()
    provider = RecordingStubASRProvider()
    session = StreamingASRSession(provider, sample_rate=sample_rate)

    events = session.push_chunk(audio) + session.flush()
    finals = [e for e in events if e.type == "final"]

    assert finals[0].utterance_id != finals[1].utterance_id
    # Fixture bursts are ~0.8s and ~0.6s; VAD frame quantization (30ms) and
    # the silence hang window mean this won't be exact, so assert a loose
    # bound rather than an exact millisecond match.
    assert finals[0].segment is not None and 500 <= finals[0].segment.end_ms <= 1200
    assert finals[1].segment is not None and 300 <= finals[1].segment.end_ms <= 1000


def test_silence_only_audio_produces_no_events() -> None:
    silence = b"\x00\x00" * 1000
    provider = RecordingStubASRProvider()
    session = StreamingASRSession(provider, sample_rate=16_000)

    events = session.push_chunk(silence)

    assert events == []
    assert provider.calls == []
