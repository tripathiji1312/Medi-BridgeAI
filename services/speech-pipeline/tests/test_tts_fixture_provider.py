import base64

import pytest

from app.tts.fixture_provider import FixtureTTSProvider


def test_returns_base64_encoded_registered_audio() -> None:
    audio = b"\x01\x02\x03\x04"
    provider = FixtureTTSProvider({"I have a fever": audio}, sample_rate=16_000)

    result = provider.synthesize("I have a fever", "en")

    assert base64.b64decode(result.audio_base64) == audio
    assert result.sample_rate == 16_000
    assert result.format == "pcm16"


def test_raises_for_unregistered_text_rather_than_silently_returning_empty() -> None:
    provider = FixtureTTSProvider({})

    with pytest.raises(KeyError):
        provider.synthesize("unregistered text", "en")
