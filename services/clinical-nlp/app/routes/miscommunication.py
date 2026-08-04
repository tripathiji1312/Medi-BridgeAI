"""HTTP endpoint for the miscommunication check (Blueprint Section 3.2 step
6). Called by speech-pipeline as an async enrichment step, the same pattern
speech-pipeline already uses internally for MT/TTS/diarization -- an HTTP
call across the service boundary is the correct way to cross it
(AGENT_INSTRUCTIONS.md Section 2: "route through an event/API contract, not
reach across and call another service's internals").

Router built via a factory so the similarity provider is injectable, same
pattern as speech-pipeline's routes.
"""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, HTTPException

from app.miscommunication.detector import MiscommunicationDetector
from app.miscommunication.provider import SimilarityProvider
from app.miscommunication.schemas import MiscommunicationCheckRequest, MiscommunicationResult


def create_miscommunication_router(
    get_similarity_provider: Callable[[], SimilarityProvider],
) -> APIRouter:
    router = APIRouter()

    @router.post("/miscommunication/check", response_model=MiscommunicationResult)
    def check_miscommunication(request: MiscommunicationCheckRequest) -> MiscommunicationResult:
        try:
            provider = get_similarity_provider()
        except RuntimeError as exc:
            # Fail loud with a well-formed error, not an opaque 500 --
            # speech-pipeline's caller degrades gracefully on this
            # (Blueprint Section 7.2), it just needs a real reason string.
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        detector = MiscommunicationDetector(provider)
        return detector.check(request.original_text, request.back_translated_text)

    return router
