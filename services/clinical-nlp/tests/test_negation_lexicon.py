from app.lexicons.negation import contains_negation


def test_detects_common_negation_marker() -> None:
    assert contains_negation("मुझे बुखार नहीं है") is True


def test_does_not_flag_text_with_no_negation_marker() -> None:
    assert contains_negation("मुझे बुखार है") is False


def test_empty_string_has_no_negation() -> None:
    assert contains_negation("") is False
