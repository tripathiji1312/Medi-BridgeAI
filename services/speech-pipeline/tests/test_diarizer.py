from app.diarization.diarizer import SpeakerDiarizer
from app.diarization.fixture_provider import FixtureEmbeddingProvider

VOICE_A_1 = b"voice-a-utterance-1"
VOICE_A_2 = b"voice-a-utterance-2"
VOICE_B_1 = b"voice-b-utterance-1"

# Two well-separated unit vectors ("distinct voices") and a near-duplicate
# of the first ("same voice again, slightly different utterance").
EMBED_A = [1.0, 0.0, 0.0]
EMBED_A_NOISY = [0.98, 0.02, 0.0]
EMBED_B = [0.0, 1.0, 0.0]


def _diarizer() -> SpeakerDiarizer:
    provider = FixtureEmbeddingProvider(
        {
            VOICE_A_1: EMBED_A,
            VOICE_A_2: EMBED_A_NOISY,
            VOICE_B_1: EMBED_B,
        }
    )
    return SpeakerDiarizer(provider)


def test_first_utterance_becomes_speaker_a_with_full_confidence() -> None:
    diarizer = _diarizer()

    result = diarizer.assign_speaker(VOICE_A_1, 16_000)

    assert result.speaker_label == "speaker_a"
    assert result.confidence == 1.0


def test_a_clearly_different_voice_becomes_speaker_b() -> None:
    diarizer = _diarizer()
    diarizer.assign_speaker(VOICE_A_1, 16_000)

    result = diarizer.assign_speaker(VOICE_B_1, 16_000)

    assert result.speaker_label == "speaker_b"


def test_a_similar_voice_is_grouped_with_the_existing_speaker_not_a_new_one() -> None:
    diarizer = _diarizer()
    diarizer.assign_speaker(VOICE_A_1, 16_000)

    result = diarizer.assign_speaker(VOICE_A_2, 16_000)

    assert result.speaker_label == "speaker_a"
    # Not a fresh seed (confidence 1.0) -- it was compared against the
    # existing centroid and found close, so confidence reflects that
    # similarity rather than being trivially maxed out.
    assert 0.0 < result.confidence < 1.0


def test_caps_at_two_speakers_folding_a_third_voice_into_the_nearer_cluster() -> None:
    diarizer = _diarizer()
    diarizer.assign_speaker(VOICE_A_1, 16_000)
    diarizer.assign_speaker(VOICE_B_1, 16_000)

    # A third, A-like voice should be folded into speaker_a (its nearest
    # existing cluster) rather than spawning a speaker_c -- this is a
    # 2-party consultation, not an open-ended multi-speaker meeting.
    result = diarizer.assign_speaker(VOICE_A_2, 16_000)

    assert result.speaker_label == "speaker_a"


def test_labeling_is_not_retroactive_earlier_calls_keep_their_original_label() -> None:
    diarizer = _diarizer()

    first = diarizer.assign_speaker(VOICE_A_1, 16_000)
    diarizer.assign_speaker(VOICE_B_1, 16_000)
    # A later, near-identical repeat of the first voice must still resolve
    # to the same label as the original call.
    third = diarizer.assign_speaker(VOICE_A_2, 16_000)

    assert first.speaker_label == third.speaker_label == "speaker_a"
