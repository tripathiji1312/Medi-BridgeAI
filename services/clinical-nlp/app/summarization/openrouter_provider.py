"""Real summarizer: Claude (Sonnet) via OpenRouter.

Architecture note (documented per AGENT_INSTRUCTIONS.md Section 1 -- a
deviation from what's already written in Blueprint Section 4 gets flagged,
not silently substituted): the blueprint specifies "Claude via Anthropic
API" directly. This build routes the same model through OpenRouter
(https://openrouter.ai), an OpenAI-API-compatible gateway, instead --
verified working with a real smoke-tested call during this session (see
docs/PROGRESS.md). The model is still Claude; only the HTTP path to reach
it differs. Kept swappable behind the Summarizer Protocol like every other
provider in this build, so a direct-Anthropic-API implementation could be
added later without touching call sites.

Import of the openai SDK (used here purely as an OpenAI-compatible HTTP
client against OpenRouter's endpoint, not to call OpenAI itself) is
deferred into __init__, same pattern as every other real provider.
"""

from __future__ import annotations

import json
import re

from app.summarization.grounding import validate_bullets
from app.summarization.provider import Summarizer
from app.summarization.schemas import StructuredSummary, SummaryBullet, SummaryUtterance

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_SUMMARY_SCHEMA_FIELDS = (
    "complaints",
    "symptoms",
    "objective",
    "diagnoses_mentioned",
    "medications",
    "recommendations",
    "action_items",
    "follow_up",
)

_CODE_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _build_prompt(utterances: list[SummaryUtterance]) -> str:
    lines = []
    for u in utterances:
        speaker = u.speaker or "unknown"
        text = u.translated_text or u.original_text
        lines.append(f'- id="{u.utterance_id}" speaker="{speaker}": {text}')
    transcript = "\n".join(lines)

    fields = ", ".join(f'"{f}": [{{"text": string, "source_utterance_id": string}}]' for f in _SUMMARY_SCHEMA_FIELDS)

    return (
        "You are assisting a clinician by summarizing a doctor-patient consultation "
        "transcript into a strict JSON object for clinical documentation. Do not "
        "diagnose, infer, or add anything not explicitly stated in the transcript -- "
        "only record what was actually said.\n\n"
        f'Output ONLY a JSON object with this exact shape: {{"patient_info": string|null, {fields}}}\n\n'
        "Rules:\n"
        "- Every bullet's source_utterance_id MUST be one of the exact id values listed below.\n"
        "- diagnoses_mentioned is only for diagnoses the patient or doctor actually said aloud, "
        "never your own assessment.\n"
        "- objective is often legitimately empty -- only include it if vitals/observations were "
        "actually stated.\n"
        "- Leave any list empty rather than inventing content to fill it.\n\n"
        f"Transcript:\n{transcript}"
    )


def _parse_json_object(raw_text: str) -> dict[str, object]:
    cleaned = _CODE_FENCE_PATTERN.sub("", raw_text.strip())
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("Model response was not a JSON object")
    return parsed


class OpenRouterSummarizer(Summarizer):
    def __init__(self, api_key: str, model_name: str = "anthropic/claude-sonnet-4.5") -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover - exercised only when the
            # optional heavy dependency isn't installed.
            raise RuntimeError(
                "openai (used as an OpenRouter-compatible client) is not installed. "
                "Install services/clinical-nlp/requirements-summarization.txt to use "
                "the real summarizer; otherwise use StaticSummarizer for "
                "MEDIBRIDGE_FIXTURE_MODE."
            ) from exc

        self._client = AsyncOpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)
        self._model_name = model_name

    async def summarize(self, utterances: list[SummaryUtterance]) -> StructuredSummary:
        prompt = _build_prompt(utterances)
        try:
            response = await self._client.chat.completions.create(
                model=self._model_name,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = response.choices[0].message.content or ""
            parsed = _parse_json_object(raw_text)
        except Exception as exc:  # noqa: BLE001 - any API/parsing failure surfaces as
            # a clear, catchable error for the route to translate into an HTTP
            # error, never a silent empty/fabricated summary.
            raise RuntimeError(f"summarization failed: {exc}") from exc

        discarded_total = 0
        field_values: dict[str, list[SummaryBullet]] = {}
        for field in _SUMMARY_SCHEMA_FIELDS:
            bullets, discarded = validate_bullets(parsed.get(field), utterances)
            field_values[field] = bullets
            discarded_total += discarded

        patient_info = parsed.get("patient_info")
        if not isinstance(patient_info, str):
            patient_info = None

        return StructuredSummary(
            patient_info=patient_info,
            discarded_ungrounded_count=discarded_total,
            model_name=self._model_name,
            **field_values,
        )
