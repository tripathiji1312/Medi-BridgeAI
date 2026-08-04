"""In-process per-session memory store. A plain dict guarded by nothing
fancier than Python's GIL is adequate for a single-process dev/demo
deployment; multi-instance/persistent storage (Postgres/Redis, per
Blueprint Section 4) is Phase 9 infra hardening, explicitly out of scope
here (Blueprint Section 6.2: work in vertical slices, don't build
persistence infra a feature doesn't need yet).

Not persisted across process restarts -- matches Section 2.2's "Persisted
per session only, cleared/archived at session end per retention policy":
clear_session() is the "cleared" half of that; real archival storage is
deferred alongside the Postgres/Redis wiring above.
"""

from __future__ import annotations

import uuid

from app.memory.schemas import (
    AddCaseMemoryEntryRequest,
    AppendUtteranceRequest,
    CaseMemoryEntry,
    SessionMemory,
    Utterance,
)


class SessionNotFoundError(KeyError):
    pass


class CaseMemoryEntryNotFoundError(KeyError):
    pass


class MemoryStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionMemory] = {}

    def _get_or_create(self, session_id: str) -> SessionMemory:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionMemory(session_id=session_id, utterances=[], case_memory=[])
        return self._sessions[session_id]

    def append_utterance(self, session_id: str, request: AppendUtteranceRequest) -> Utterance:
        memory = self._get_or_create(session_id)
        utterance = Utterance(
            id=uuid.uuid4().hex,
            speaker=request.speaker,
            original_text=request.original_text,
            translated_text=request.translated_text,
            sequence=len(memory.utterances),
        )
        memory.utterances.append(utterance)
        return utterance

    def add_case_memory_entry(self, session_id: str, request: AddCaseMemoryEntryRequest) -> CaseMemoryEntry:
        memory = self._get_or_create(session_id)
        entry = CaseMemoryEntry(
            id=uuid.uuid4().hex,
            category=request.category,
            value=request.value,
            source_utterance_id=request.source_utterance_id,
        )
        memory.case_memory.append(entry)
        return entry

    def remove_case_memory_entry(self, session_id: str, entry_id: str) -> None:
        """Clinician-editable removal (Blueprint Section 2.4: "explicit
        chips, editable/removable by clinician") -- raises rather than
        silently no-op-ing on an unknown id, so a UI bug (double-click,
        stale state) surfaces instead of hiding a real problem."""
        if session_id not in self._sessions:
            raise SessionNotFoundError(session_id)
        memory = self._sessions[session_id]
        before = len(memory.case_memory)
        memory.case_memory = [e for e in memory.case_memory if e.id != entry_id]
        if len(memory.case_memory) == before:
            raise CaseMemoryEntryNotFoundError(entry_id)

    def get_memory(self, session_id: str) -> SessionMemory:
        if session_id not in self._sessions:
            raise SessionNotFoundError(session_id)
        return self._sessions[session_id]

    def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
