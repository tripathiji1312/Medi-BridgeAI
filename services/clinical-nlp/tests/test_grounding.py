from app.summarization.grounding import validate_bullets
from app.summarization.schemas import SummaryUtterance

UTTERANCES = [
    SummaryUtterance(
        utterance_id="u1", speaker="patient", original_text="मुझे बुखार है", translated_text="I have a fever"
    ),
    SummaryUtterance(
        utterance_id="u2",
        speaker="patient",
        original_text="मैं पैरासिटामोल ले रहा हूं",
        translated_text="I am taking paracetamol",
    ),
]


def test_valid_grounded_bullet_is_accepted() -> None:
    raw = [{"text": "Patient reports fever", "source_utterance_id": "u1"}]

    bullets, discarded = validate_bullets(raw, UTTERANCES)

    assert len(bullets) == 1
    assert bullets[0].source_utterance_id == "u1"
    assert discarded == 0


def test_citation_to_a_nonexistent_utterance_id_is_discarded() -> None:
    # Blueprint Section 11.1: "If an LLM-based extractor cannot produce a
    # valid span match, the item is discarded, not shown."
    raw = [{"text": "Patient reports fever", "source_utterance_id": "u99-does-not-exist"}]

    bullets, discarded = validate_bullets(raw, UTTERANCES)

    assert bullets == []
    assert discarded == 1


def test_a_valid_id_but_unrelated_content_is_discarded_by_the_lexical_backstop() -> None:
    # Cites u1 (about fever) but writes content that actually belongs to a
    # completely different topic -- the lexical overlap backstop should
    # catch this even though the id itself is structurally valid.
    raw = [{"text": "surgery scheduled next month for knee replacement procedure", "source_utterance_id": "u1"}]

    bullets, discarded = validate_bullets(raw, UTTERANCES)

    assert bullets == []
    assert discarded == 1


def test_malformed_candidates_are_discarded_not_crashed_on() -> None:
    raw = [
        "not a dict",
        {"text": "", "source_utterance_id": "u1"},  # empty text
        {"source_utterance_id": "u1"},  # missing text
        {"text": "fever"},  # missing source_utterance_id
        {"text": "fever", "source_utterance_id": 123},  # wrong type
        None,
    ]

    bullets, discarded = validate_bullets(raw, UTTERANCES)

    assert bullets == []
    assert discarded == 6


def test_non_list_input_discards_nothing_and_returns_empty() -> None:
    bullets, discarded = validate_bullets("not a list", UTTERANCES)

    assert bullets == []
    assert discarded == 0


def test_multiple_valid_bullets_across_different_utterances() -> None:
    raw = [
        {"text": "Patient has a fever", "source_utterance_id": "u1"},
        {"text": "Patient is taking paracetamol", "source_utterance_id": "u2"},
    ]

    bullets, discarded = validate_bullets(raw, UTTERANCES)

    assert len(bullets) == 2
    assert discarded == 0
    assert {b.source_utterance_id for b in bullets} == {"u1", "u2"}


def test_mixed_valid_and_invalid_bullets_keeps_only_the_valid_ones() -> None:
    raw = [
        {"text": "Patient has a fever", "source_utterance_id": "u1"},
        {"text": "Patient has a fever", "source_utterance_id": "u-bogus"},
    ]

    bullets, discarded = validate_bullets(raw, UTTERANCES)

    assert len(bullets) == 1
    assert bullets[0].source_utterance_id == "u1"
    assert discarded == 1
