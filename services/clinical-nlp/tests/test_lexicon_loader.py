from app.lexicons.loader import load_lexicon


def test_lexicon_loads_with_a_version_and_terms() -> None:
    lexicon = load_lexicon()

    assert lexicon.version
    assert len(lexicon.terms) > 0


def test_every_term_has_at_least_one_hindi_and_one_english_variant() -> None:
    lexicon = load_lexicon()

    for term in lexicon.terms:
        assert len(term.hindi) >= 1, f"{term.canonical} has no Hindi variant"
        assert len(term.english) >= 1, f"{term.canonical} has no English variant"


def test_all_six_categories_are_represented() -> None:
    lexicon = load_lexicon()

    categories = {term.category for term in lexicon.terms}
    assert categories == {"symptom", "disease", "medication", "allergy", "vital_sign", "procedure"}


def test_load_lexicon_is_cached_returns_the_same_object() -> None:
    assert load_lexicon() is load_lexicon()
