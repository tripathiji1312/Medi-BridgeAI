"""REST API for session conversation memory (Blueprint Section 2.2/2.4).
Router built via a factory so the store is injectable in tests, same
pattern used throughout this build."""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, HTTPException

from app.memory.schemas import (
    AddCaseMemoryEntryRequest,
    AddDismissedAlertRequest,
    AppendUtteranceRequest,
    CaseMemoryEntry,
    DismissedAlert,
    SessionMemory,
    Utterance,
)
from app.memory.store import CaseMemoryEntryNotFoundError, MemoryStore, SessionNotFoundError


def create_memory_router(get_store: Callable[[], MemoryStore]) -> APIRouter:
    router = APIRouter()

    @router.post("/sessions/{session_id}/utterances", response_model=Utterance)
    def append_utterance(session_id: str, request: AppendUtteranceRequest) -> Utterance:
        return get_store().append_utterance(session_id, request)

    @router.get("/sessions/{session_id}/memory", response_model=SessionMemory)
    def get_memory(session_id: str) -> SessionMemory:
        try:
            return get_store().get_memory(session_id)
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"No session found: {session_id}") from exc

    @router.post("/sessions/{session_id}/case-memory", response_model=CaseMemoryEntry)
    def add_case_memory_entry(session_id: str, request: AddCaseMemoryEntryRequest) -> CaseMemoryEntry:
        return get_store().add_case_memory_entry(session_id, request)

    @router.delete("/sessions/{session_id}/case-memory/{entry_id}", status_code=204)
    def remove_case_memory_entry(session_id: str, entry_id: str) -> None:
        try:
            get_store().remove_case_memory_entry(session_id, entry_id)
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"No session found: {session_id}") from exc
        except CaseMemoryEntryNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"No case-memory entry found: {entry_id}") from exc

    @router.post("/sessions/{session_id}/dismissed-alerts", response_model=DismissedAlert)
    def add_dismissed_alert(session_id: str, request: AddDismissedAlertRequest) -> DismissedAlert:
        return get_store().add_dismissed_alert(session_id, request)

    @router.delete("/sessions/{session_id}", status_code=204)
    def clear_session(session_id: str) -> None:
        get_store().clear_session(session_id)

    return router
