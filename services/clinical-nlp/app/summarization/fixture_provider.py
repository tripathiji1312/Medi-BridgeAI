"""Deterministic summarizer test doubles -- mirrors the Fixture/Static split
used by every other real-model provider in this build."""

from __future__ import annotations

import hashlib
import json

from app.summarization.provider import Summarizer
from app.summarization.schemas import StructuredSummary, SummaryBullet, SummaryUtterance


def _digest(utterances: list[SummaryUtterance]) -> str:
    payload = json.dumps([u.model_dump() for u in utterances], sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class FixtureSummarizer(Summarizer):
    """Keyed by a digest of the exact utterance list -- mirrors
    app.asr.fixture_provider.FixtureASRProvider's role for tests that
    assert on specific input."""

    def __init__(self, fixtures: dict[str, StructuredSummary]) -> None:
        self._fixtures = fixtures

    async def summarize(self, utterances: list[SummaryUtterance]) -> StructuredSummary:
        digest = _digest(utterances)
        if digest not in self._fixtures:
            raise KeyError(f"No fixture registered for utterance digest {digest}")
        return self._fixtures[digest]


class StaticSummarizer(Summarizer):
    """Always returns the same shape of canned summary regardless of
    content, citing only the first given utterance (if any) so the output
    stays structurally grounded -- used to run the real server
    deterministically under MEDIBRIDGE_FIXTURE_MODE without calling
    OpenRouter."""

    async def summarize(self, utterances: list[SummaryUtterance]) -> StructuredSummary:
        if not utterances:
            return StructuredSummary(
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
                model_name="static-fixture",
            )

        first_id = utterances[0].utterance_id
        return StructuredSummary(
            patient_info=None,
            complaints=[
                SummaryBullet(
                    text="Fixture mode: deterministic canned summary, not derived from real content.",
                    source_utterance_id=first_id,
                )
            ],
            symptoms=[],
            objective=[],
            diagnoses_mentioned=[],
            medications=[],
            recommendations=[],
            action_items=[],
            follow_up=[],
            discarded_ungrounded_count=0,
            model_name="static-fixture",
        )
