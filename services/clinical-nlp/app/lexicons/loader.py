"""Loads the curated medical term lexicon (Blueprint Section 11.1:
"deterministic lexicon backstop"). The JSON lives alongside this module so
it ships with the service with no cross-package/Docker-copy complexity --
see packages/medical-lexicon/README.md for why that package isn't the
source of truth here."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

EntityCategory = Literal["symptom", "disease", "medication", "allergy", "vital_sign", "procedure"]

_LEXICON_PATH = Path(__file__).parent / "medical_terms.json"


class LexiconTerm(BaseModel):
    model_config = {"strict": True}

    canonical: str
    category: EntityCategory
    icd10: str | None
    hindi: list[str]
    english: list[str]
    definition: str
    is_emergency_keyword: bool


class MedicalLexicon(BaseModel):
    model_config = {"strict": True}

    version: str
    terms: list[LexiconTerm]


@lru_cache(maxsize=1)
def load_lexicon() -> MedicalLexicon:
    data = json.loads(_LEXICON_PATH.read_text(encoding="utf-8"))
    return MedicalLexicon.model_validate(data)
