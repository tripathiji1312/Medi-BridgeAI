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


class SessionMemory(BaseModel):
    """Rolling context (utterances) + structured case memory. Case memory
    is populated by Phase 5's NER/symptom-extraction calling
    POST /sessions/{id}/case-memory -- this phase provides the store and
    API, not the extraction itself (that's clinical-nlp's job, not
    orchestrator's, per AGENT_INSTRUCTIONS.md's service boundary table)."""

    model_config = {"strict": True}

    session_id: str
    utterances: list[Utterance]
    case_memory: list[CaseMemoryEntry]
