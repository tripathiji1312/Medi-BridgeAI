from app.lexicons.loader import LexiconTerm, MedicalLexicon
from app.risk_scoring.scorer import compute_raw_risk

FEVER_TERM = LexiconTerm(
    canonical="fever",
    category="symptom",
    icd10="R50.9",
    hindi=["बुखार"],
    english=["fever"],
    definition="An elevated body temperature.",
    is_emergency_keyword=False,
)
COUGH_TERM = LexiconTerm(
    canonical="cough",
    category="symptom",
    icd10="R05",
    hindi=["खांसी"],
    english=["cough"],
    definition="A reflex to clear the airway.",
    is_emergency_keyword=False,
)
CHEST_PAIN_TERM = LexiconTerm(
    canonical="chest pain",
    category="symptom",
    icd10="R07.9",
    hindi=["सीने में दर्द"],
    english=["chest pain"],
    definition="Pain in the chest.",
    is_emergency_keyword=True,
)


def _lexicon(*terms: LexiconTerm) -> MedicalLexicon:
    return MedicalLexicon(version="test", terms=list(terms))


def test_no_symptoms_scores_low_with_a_reason() -> None:
    level, reason, count, emergency = compute_raw_risk("nice weather today", _lexicon(FEVER_TERM), None, None)

    assert level == "low"
    assert count == 0
    assert emergency is False
    assert "No symptoms" in reason


def test_single_symptom_scores_low() -> None:
    level, reason, count, emergency = compute_raw_risk("I have a fever", _lexicon(FEVER_TERM), None, None)

    assert level == "low"
    assert count == 1
    assert "fever" in reason


def test_two_symptoms_scores_medium_naming_both() -> None:
    level, reason, count, emergency = compute_raw_risk(
        "I have a fever and a cough", _lexicon(FEVER_TERM, COUGH_TERM), None, None
    )

    assert level == "medium"
    assert count == 2
    assert "fever" in reason and "cough" in reason


def test_one_symptom_plus_concerning_emotion_scores_medium() -> None:
    level, reason, count, emergency = compute_raw_risk(
        "I have a fever", _lexicon(FEVER_TERM), "anxious", 0.8
    )

    assert level == "medium"
    assert "anxious" in reason


def test_low_confidence_emotion_does_not_escalate_a_single_symptom() -> None:
    # Blueprint's "don't let a low-confidence signal drive a high-stakes
    # decision" principle applied to the emotion input specifically.
    level, _, _, _ = compute_raw_risk("I have a fever", _lexicon(FEVER_TERM), "anxious", 0.2)

    assert level == "low"


def test_non_concerning_emotion_does_not_escalate() -> None:
    level, _, _, _ = compute_raw_risk("I have a fever", _lexicon(FEVER_TERM), "happy", 0.95)

    assert level == "low"


def test_emergency_keyword_forces_high_regardless_of_symptom_count() -> None:
    level, reason, _, emergency = compute_raw_risk(
        "I have chest pain", _lexicon(CHEST_PAIN_TERM), None, None
    )

    assert level == "high"
    assert emergency is True
    assert "chest pain" in reason


def test_emergency_keyword_forces_high_even_with_low_confidence_asr() -> None:
    # Blueprint Section 12.2: emergency alerting is not gated by general
    # confidence -- this function doesn't even take an ASR confidence
    # parameter, which is itself the guarantee; this test documents that
    # intent explicitly rather than leaving it implicit.
    level, _, _, emergency = compute_raw_risk("I have chest pain", _lexicon(CHEST_PAIN_TERM), None, None)

    assert level == "high"
    assert emergency is True
