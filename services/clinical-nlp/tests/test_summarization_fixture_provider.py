import asyncio

import pytest

from app.summarization.fixture_provider import FixtureSummarizer, StaticSummarizer, _digest
from app.summarization.schemas import StructuredSummary, SummaryUtterance

UTTERANCES = [
    SummaryUtterance(utterance_id="u1", speaker="patient", original_text="मुझे बुखार है", translated_text="I have a fever")
]

EMPTY_SUMMARY = StructuredSummary(
    patient_info=None,
    complaints=[],
    symptoms=[],
    objective=[],
    diagnoses_mentioned=[],
    medications=[],
    recommendations=[],
    action_items=[],
    follow_up=[],
    discarded_ungrounded_count=0,
    model_name="fixture",
)


def test_fixture_summarizer_returns_the_registered_summary_for_the_exact_utterance_digest() -> None:
    digest = _digest(UTTERANCES)
    summarizer = FixtureSummarizer({digest: EMPTY_SUMMARY})

    result = asyncio.run(summarizer.summarize(UTTERANCES))

    assert result == EMPTY_SUMMARY


def test_fixture_summarizer_raises_for_unregistered_utterances() -> None:
    summarizer = FixtureSummarizer({})

    with pytest.raises(KeyError):
        asyncio.run(summarizer.summarize(UTTERANCES))


def test_static_summarizer_returns_a_grounded_bullet_citing_the_first_utterance() -> None:
    summarizer = StaticSummarizer()

    result = asyncio.run(summarizer.summarize(UTTERANCES))

    assert len(result.complaints) == 1
    assert result.complaints[0].source_utterance_id == "u1"
    assert result.model_name == "static-fixture"


def test_static_summarizer_handles_no_utterances_without_error() -> None:
    summarizer = StaticSummarizer()

    result = asyncio.run(summarizer.summarize([]))

    assert result.complaints == []
    assert result.discarded_ungrounded_count == 0
