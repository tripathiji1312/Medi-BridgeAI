from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CaseMemoryCategory = Literal["symptom", "medication", "allergy"]


class AppendUtteranceRequest(BaseModel):
    model_config = {"strict": True}

    speaker: str | None = None
    original_text: str
    translated_text: str | None = None


class Utterance(BaseModel):
    model_config = {"strict": True}

    id: str
    speaker: str | None
    original_text: str
    translated_text: str | None
    sequence: int = Field(ge=0)


class AddCaseMemoryEntryRequest(BaseModel):
    """`source_utterance_id` links the entry back to the transcript span it
    came from (Blueprint Section 11.1: "grounding via span citation" --
    every extracted entity carries a reference to where it came from)."""

    model_config = {"strict": True}

    category: CaseMemoryCategory
    value: str
    source_utterance_id: str | None = None


class CaseMemoryEntry(BaseModel):
    model_config = {"strict": True}

    id: str
    category: CaseMemoryCategory
    value: str
    source_utterance_id: str | None


class AddDismissedAlertRequest(BaseModel):
    """Blueprint Section 2.2: emergency alerts require "easy dismissal
    logged for audit" -- a clinician must always give a reason to dismiss
    (never a bare click-to-clear), and that reason must be recorded, not
    discarded once the banner disappears from screen."""

    model_config = {"strict": True}

    reason: str
    source_utterance_id: str | None = None


class DismissedAlert(BaseModel):
    model_config = {"strict": True}

    id: str
    reason: str
    source_utterance_id: str | None


class SessionMemory(BaseModel):
    """Rolling context (utterances) + structured case memory + dismissed
    emergency alerts. Case memory is populated by Phase 5's NER/symptom-
    extraction calling POST /sessions/{id}/case-memory -- this phase
    provides the store and API, not the extraction itself (that's
    clinical-nlp's job, not orchestrator's, per AGENT_INSTRUCTIONS.md's
    service boundary table).

    dismissed_alerts is a minimal, session-scoped precursor to Phase 9's
    full "immutable append-only audit log" (see app/audit/__init__.py) --
    deliberately not that system. It exists now because Blueprint Section
    2.2's emergency-alert dismissal requirement can't honestly be skipped
    until Phase 9, but it makes no claim to immutability, cross-session
    audit trails, or long-term retention -- those are still Phase 9 scope."""

    model_config = {"strict": True}

    session_id: str
    utterances: list[Utterance]
    case_memory: list[CaseMemoryEntry]
    dismissed_alerts: list[DismissedAlert]
