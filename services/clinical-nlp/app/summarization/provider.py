from __future__ import annotations

from typing import Protocol

from app.summarization.schemas import StructuredSummary, SummaryUtterance


class Summarizer(Protocol):
    async def summarize(self, utterances: list[SummaryUtterance]) -> StructuredSummary: ...
