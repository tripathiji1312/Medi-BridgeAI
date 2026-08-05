"""HTTP endpoint for LLM-backed structured summarization (Blueprint Section
2.2/2.4). Router built via a factory so the summarizer is injectable in
tests, same pattern used throughout this build."""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, HTTPException

from app.summarization.provider import Summarizer
from app.summarization.schemas import StructuredSummary, SummarizeRequest


def create_summarization_router(get_summarizer: Callable[[], Summarizer]) -> APIRouter:
    router = APIRouter()

    @router.post("/summarize", response_model=StructuredSummary)
    async def summarize(request: SummarizeRequest) -> StructuredSummary:
        try:
            return await get_summarizer().summarize(request.utterances)
        except RuntimeError as exc:
            # Fail loud, not silent (Blueprint Section 1 Principle 3): the
            # caller (orchestrator) needs to know summarization failed, not
            # receive a fabricated or empty-but-unlabeled summary.
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    return router
