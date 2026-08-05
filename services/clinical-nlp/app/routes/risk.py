"""HTTP endpoint for risk scoring (Blueprint Section 2.2). Router built via
a factory so the hysteresis store is injectable in tests, same pattern used
throughout this build (see app/main.py for the module-level singleton this
is wired to in the real app)."""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter

from app.lexicons.loader import load_lexicon
from app.risk_scoring.hysteresis import RiskHistoryStore
from app.risk_scoring.schemas import RiskAssessment, RiskScoreRequest
from app.risk_scoring.scorer import compute_raw_risk


def create_risk_router(get_store: Callable[[], RiskHistoryStore]) -> APIRouter:
    router = APIRouter()

    @router.post("/risk/score", response_model=RiskAssessment)
    def score(request: RiskScoreRequest) -> RiskAssessment:
        lexicon = load_lexicon()
        raw_level, reason, symptom_count, emergency_triggered = compute_raw_risk(
            request.text, lexicon, request.emotion_label, request.emotion_confidence
        )
        level = get_store().step(request.session_id, raw_level, emergency_triggered)
        return RiskAssessment(
            level=level,
            raw_level=raw_level,
            reason=reason,
            emergency_triggered=emergency_triggered,
            symptom_count=symptom_count,
            lexicon_version=lexicon.version,
        )

    @router.delete("/risk/sessions/{session_id}", status_code=204)
    def clear_session(session_id: str) -> None:
        get_store().clear_session(session_id)

    return router
