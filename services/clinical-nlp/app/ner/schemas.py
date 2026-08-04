from __future__ import annotations

from pydantic import BaseModel, Field

from app.lexicons.loader import EntityCategory


class MedicalEntity(BaseModel):
    """`text`/`start_char`/`end_char` are the exact matched substring and
    its position in the input -- grounding via span citation (Blueprint
    Section 11.1): a client can always highlight exactly what was matched,
    never a paraphrase or a hallucinated mention."""

    model_config = {"strict": True}

    text: str
    category: EntityCategory
    canonical_name: str
    canonical_code: str | None
    definition: str
    confidence: float = Field(ge=0.0, le=1.0)
    start_char: int = Field(ge=0)
    end_char: int = Field(ge=0)
    is_fuzzy_match: bool


class EntityExtractionRequest(BaseModel):
    model_config = {"strict": True}

    text: str
    language: str = "hi"


class EntityExtractionResponse(BaseModel):
    model_config = {"strict": True}

    entities: list[MedicalEntity]
    # Every AI-derived value is versioned (Blueprint Section 3.3) so a
    # client/audit trail can tell which lexicon revision produced a match.
    lexicon_version: str
