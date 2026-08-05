"""HTTP endpoint for emergency keyword/phrase detection (Blueprint Section
2.2/2.4). Same "no injectable provider" reasoning as entities.py -- lexicon
matching is local and deterministic, nothing to swap or degrade.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.emergency_detector.detector import build_reason, detect_emergency
from app.emergency_detector.schemas import EmergencyDetectionRequest, EmergencyDetectionResponse
from app.lexicons.loader import load_lexicon


def create_emergency_router() -> APIRouter:
    router = APIRouter()

    @router.post("/emergency/detect", response_model=EmergencyDetectionResponse)
    def detect(request: EmergencyDetectionRequest) -> EmergencyDetectionResponse:
        lexicon = load_lexicon()
        matches = detect_emergency(request.text, lexicon)
        return EmergencyDetectionResponse(
            alert=len(matches) > 0,
            matches=matches,
            reason=build_reason(matches),
            lexicon_version=lexicon.version,
        )

    return router
