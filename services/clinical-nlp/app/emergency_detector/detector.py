"""Emergency keyword/phrase detection (Blueprint Section 2.2/2.4: "keyword/
phrase trigger list ... FAST criteria"). Deliberately its own function, not
"filter the general entity-extraction results" -- this path gates a
safety-critical alert (Blueprint Section 3.2 step 10: emergency keyword hits
short-circuit the pipeline and must not wait on the full NLP pass), so it
must stay simple, self-contained, and independently verifiable rather than
implicitly depending on whatever else the general NER pass happens to do or
how it's scoped.

Reuses app.ner.extractor's matching engine (exact + fuzzy, span-grounded,
overlap-resolved) rather than duplicating that logic, but only against the
subset of lexicon terms flagged is_emergency_keyword -- same deterministic
lexicon backstop principle (Blueprint Section 11.1), scoped to the trigger
list.
"""

from __future__ import annotations

from app.lexicons.loader import MedicalLexicon
from app.ner.extractor import extract_entities
from app.ner.schemas import MedicalEntity


def detect_emergency(text: str, lexicon: MedicalLexicon) -> list[MedicalEntity]:
    emergency_terms = [term for term in lexicon.terms if term.is_emergency_keyword]
    if not emergency_terms:
        return []
    emergency_lexicon = lexicon.model_copy(update={"terms": emergency_terms})
    return extract_entities(text, emergency_lexicon)


def build_reason(matches: list[MedicalEntity]) -> str | None:
    if not matches:
        return None
    names = ", ".join(sorted({m.canonical_name for m in matches}))
    return f"Detected emergency keyword(s): {names}."
