from app.emergency_detector.detector import build_reason, detect_emergency
from app.lexicons.loader import LexiconTerm, MedicalLexicon, load_lexicon

CHEST_PAIN_TERM = LexiconTerm(
    canonical="chest pain",
    category="symptom",
    icd10="R07.9",
    hindi=["सीने में दर्द"],
    english=["chest pain"],
    definition="Pain in the chest.",
    is_emergency_keyword=True,
)
FEVER_TERM = LexiconTerm(
    canonical="fever",
    category="symptom",
    icd10="R50.9",
    hindi=["बुखार"],
    english=["fever"],
    definition="An elevated body temperature.",
    is_emergency_keyword=False,
)


def _lexicon(*terms: LexiconTerm) -> MedicalLexicon:
    return MedicalLexicon(version="test", terms=list(terms))


def test_matches_a_flagged_emergency_term() -> None:
    matches = detect_emergency("I have chest pain", _lexicon(CHEST_PAIN_TERM, FEVER_TERM))

    assert len(matches) == 1
    assert matches[0].canonical_name == "chest pain"


def test_ignores_non_emergency_terms_entirely() -> None:
    matches = detect_emergency("I have a fever", _lexicon(CHEST_PAIN_TERM, FEVER_TERM))

    assert matches == []


def test_no_emergency_terms_in_lexicon_returns_empty_without_error() -> None:
    matches = detect_emergency("I have a fever", _lexicon(FEVER_TERM))

    assert matches == []


def test_unrelated_speech_containing_a_trigger_word_in_non_medical_context() -> None:
    # Blueprint Section 12.2 negative case: "chest of drawers" contains
    # "chest" but not the "chest pain" phrase -- documented, explicitly
    # tested choice: this build accepts the conservative false positive if
    # a full trigger phrase actually matches, but a single word ("chest")
    # alone must not, since the lexicon entry is the multi-word phrase
    # "chest pain", not "chest".
    matches = detect_emergency("I bought a chest of drawers", _lexicon(CHEST_PAIN_TERM))

    assert matches == []


def test_build_reason_names_the_matched_term() -> None:
    matches = detect_emergency("I have chest pain", _lexicon(CHEST_PAIN_TERM))

    reason = build_reason(matches)

    assert reason is not None
    assert "chest pain" in reason


def test_build_reason_is_none_when_no_matches() -> None:
    assert build_reason([]) is None


def test_fast_criteria_terms_are_flagged_emergency_in_the_real_lexicon() -> None:
    lexicon = load_lexicon()
    canonicals = {t.canonical for t in lexicon.terms if t.is_emergency_keyword}

    for expected in {
        "chest pain",
        "shortness of breath",
        "unconsciousness",
        "severe bleeding",
        "facial drooping",
        "one-sided weakness",
        "slurred speech",
        "stroke",
    }:
        assert expected in canonicals


def test_real_lexicon_detects_stroke_fast_criteria_phrase() -> None:
    lexicon = load_lexicon()

    matches = detect_emergency("His face is drooping on one side and his speech is slurred", lexicon)

    names = {m.canonical_name for m in matches}
    assert "facial drooping" in names
    assert "slurred speech" in names
