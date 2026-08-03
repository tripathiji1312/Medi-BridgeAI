import pytest

from app.asr.fixture_provider import FixtureASRProvider, StaticASRProvider
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


def test_static_provider_returns_the_same_canned_text_for_any_audio() -> None:
    provider = StaticASRProvider(text="fixed text", confidence=0.5, language="hi")

    result_a = provider.transcribe(b"\x01\x02" * 100, sample_rate=16_000)
    result_b = provider.transcribe(b"\xff\xee" * 50, sample_rate=16_000)

    assert result_a[0].text == result_b[0].text == "fixed text"
    assert result_a[0].confidence == 0.5
