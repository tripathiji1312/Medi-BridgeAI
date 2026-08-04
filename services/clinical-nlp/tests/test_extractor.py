from app.lexicons.loader import LexiconTerm, MedicalLexicon, load_lexicon
from app.ner.extractor import extract_entities

FEVER_TERM = LexiconTerm(
    canonical="fever",
    category="symptom",
    icd10="R50.9",
    hindi=["बुखार"],
    english=["fever"],
    definition="An elevated body temperature.",
    is_emergency_keyword=False,
)
HEADACHE_TERM = LexiconTerm(
    canonical="headache",
    category="symptom",
    icd10="R51",
    hindi=["सिरदर्द"],
    english=["headache"],
    definition="Pain in the head.",
    is_emergency_keyword=False,
)


def _lexicon(*terms: LexiconTerm) -> MedicalLexicon:
    return MedicalLexicon(version="test", terms=list(terms))


def test_exact_match_has_full_confidence_and_correct_span() -> None:
    text = "मुझे बुखार है"
    entities = extract_entities(text, _lexicon(FEVER_TERM))

    assert len(entities) == 1
    entity = entities[0]
    assert entity.text == "बुखार"
    assert entity.canonical_name == "fever"
    assert entity.category == "symptom"
    assert entity.canonical_code == "R50.9"
    assert entity.confidence == 1.0
    assert entity.is_fuzzy_match is False
    # Grounding: the reported span must actually be that substring in the source text.
    assert text[entity.start_char : entity.end_char] == "बुखार"


def test_english_variant_also_matches() -> None:
    entities = extract_entities("I have a fever", _lexicon(FEVER_TERM))

    assert len(entities) == 1
    assert entities[0].canonical_name == "fever"


def test_misspelled_term_still_fuzzy_matches_with_lower_confidence() -> None:
    # Blueprint Section 12.1: "given a sentence with a medicine name
    # misspelled/mispronounced, verify fuzzy-match against lexicon still
    # finds a candidate with lower confidence, not silently dropped."
    entities = extract_entities("I have a fevr", _lexicon(FEVER_TERM))

    assert len(entities) == 1
    assert entities[0].canonical_name == "fever"
    assert entities[0].is_fuzzy_match is True
    assert 0.0 < entities[0].confidence < 1.0


def test_unrelated_text_produces_no_entities_rather_than_a_forced_match() -> None:
    entities = extract_entities("the weather is nice today", _lexicon(FEVER_TERM))

    assert entities == []


def test_multiple_distinct_entities_in_one_sentence_are_all_found() -> None:
    text = "मुझे बुखार और सिरदर्द है"
    entities = extract_entities(text, _lexicon(FEVER_TERM, HEADACHE_TERM))

    names = {e.canonical_name for e in entities}
    assert names == {"fever", "headache"}
    for entity in entities:
        assert text[entity.start_char : entity.end_char] == entity.text


def test_overlapping_candidates_keep_only_the_higher_confidence_one() -> None:
    # "headache" and a near-duplicate lower-quality variant of the same
    # term shouldn't both survive for the same span.
    near_duplicate = LexiconTerm(
        canonical="head pain (near-duplicate)",
        category="symptom",
        icd10=None,
        hindi=[],
        english=["headach"],  # close enough to fuzzy-match "headache"
        definition="duplicate for overlap testing",
        is_emergency_keyword=False,
    )
    entities = extract_entities("I have a headache", _lexicon(HEADACHE_TERM, near_duplicate))

    # Only one entity should be reported for that span, not two competing ones.
    assert len(entities) == 1
    assert entities[0].confidence == 1.0
    assert entities[0].canonical_name == "headache"


def test_entities_are_returned_in_left_to_right_order() -> None:
    text = "सिरदर्द है और बुखार भी है"
    entities = extract_entities(text, _lexicon(FEVER_TERM, HEADACHE_TERM))

    assert [e.canonical_name for e in entities] == ["headache", "fever"]


def test_real_lexicon_extracts_a_realistic_clinical_sentence() -> None:
    lexicon = load_lexicon()
    text = "मुझे तीन दिन से बुखार और सिरदर्द है"

    entities = extract_entities(text, lexicon)

    names = {e.canonical_name for e in entities}
    assert "fever" in names
    assert "headache" in names
