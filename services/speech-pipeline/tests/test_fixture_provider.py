import pytest

from app.asr.fixture_provider import FixtureASRProvider
from app.asr.schemas import TranscriptSegment


def test_returns_registered_segments_for_matching_audio() -> None:
    audio = b"\x01\x02" * 100
    expected = [
        TranscriptSegment(text="hello", is_final=True, confidence=0.95, start_ms=0, end_ms=100, language="hi")
    ]
    provider = FixtureASRProvider({__digest(audio): expected})

    result = provider.transcribe(audio, sample_rate=16_000)

    assert result == expected


def test_raises_for_unregistered_audio_rather_than_silently_returning_empty() -> None:
    provider = FixtureASRProvider({})

    with pytest.raises(KeyError):
        provider.transcribe(b"\x00\x00", sample_rate=16_000)


def __digest(audio: bytes) -> str:
    import hashlib

    return hashlib.sha256(audio).hexdigest()
