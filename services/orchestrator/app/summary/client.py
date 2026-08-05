"""Client for clinical-nlp's LLM-backed summarizer. Orchestrator calling
another service's HTTP endpoint is orchestration (its whole purpose, per
Blueprint Section 3.2 step 9: "Orchestration service merges all outputs"),
not "direct ML inference" (AGENT_INSTRUCTIONS.md Section 2's actual
prohibition is running/hosting a model here, not calling one elsewhere).
Same Protocol + real-impl + factory pattern as every cross-service client
in this build."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Protocol

import httpx

from app.memory.schemas import Utterance
from app.summary.schemas import StructuredSummary


class ClinicalNlpSummarizer(Protocol):
    async def summarize(self, utterances: list[Utterance]) -> StructuredSummary: ...


class HttpClinicalNlpSummarizer(ClinicalNlpSummarizer):
    def __init__(self, base_url: str, timeout_seconds: float = 30.0) -> None:
        # A real LLM call is slower than the sub-second local-model calls
        # elsewhere in this build -- 30s, not the usual 5s, so a summary
        # request that's genuinely still in flight isn't mistaken for a
        # hung one.
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def summarize(self, utterances: list[Utterance]) -> StructuredSummary:
        payload = {
            "utterances": [
                {
                    "utterance_id": u.id,
                    "speaker": u.speaker,
                    "original_text": u.original_text,
                    "translated_text": u.translated_text,
                }
                for u in utterances
            ]
        }
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            try:
                response = await client.post(f"{self._base_url}/summarize", json=payload)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise RuntimeError(f"clinical-nlp unavailable: {exc}") from exc
        return StructuredSummary.model_validate(response.json())


@lru_cache(maxsize=1)
def get_summarizer_client() -> ClinicalNlpSummarizer:
    base_url = os.environ.get("CLINICAL_NLP_URL", "http://localhost:8002")
    return HttpClinicalNlpSummarizer(base_url=base_url)
