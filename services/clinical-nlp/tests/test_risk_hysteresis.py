from app.risk_scoring.hysteresis import RiskHistoryStore


def test_first_observation_is_shown_immediately() -> None:
    store = RiskHistoryStore()

    level = store.step("s1", "medium", False)

    assert level == "medium"


def test_single_turn_flip_does_not_change_the_displayed_level() -> None:
    # Blueprint Section 12.1: "verify hysteresis prevents single-turn flip."
    store = RiskHistoryStore()
    store.step("s1", "low", False)

    level = store.step("s1", "high", False)

    assert level == "low"


def test_sustained_evidence_over_two_turns_does_escalate() -> None:
    # Blueprint Section 12.1: "verify it does escalate appropriately over
    # sustained evidence."
    store = RiskHistoryStore()
    store.step("s1", "low", False)
    store.step("s1", "medium", False)  # 1st medium -- not enough yet

    level = store.step("s1", "medium", False)  # 2nd consecutive medium -- escalates

    assert level == "medium"


def test_a_single_low_turn_between_two_mediums_resets_the_confirmation_count() -> None:
    store = RiskHistoryStore()
    store.step("s1", "low", False)
    store.step("s1", "medium", False)
    store.step("s1", "low", False)  # interrupts the streak

    level = store.step("s1", "medium", False)  # only the 1st medium again after the interruption

    assert level == "low"


def test_de_escalation_also_requires_two_consecutive_turns() -> None:
    store = RiskHistoryStore()
    store.step("s1", "medium", False)
    store.step("s1", "medium", False)

    level = store.step("s1", "low", False)  # 1st low -- not enough yet

    assert level == "medium"

    level = store.step("s1", "low", False)  # 2nd consecutive low -- de-escalates

    assert level == "low"


def test_emergency_forces_high_immediately_bypassing_confirmation() -> None:
    # Blueprint Section 12.2: emergency alerts are never held back waiting
    # for a second confirming turn.
    store = RiskHistoryStore()
    store.step("s1", "low", False)

    level = store.step("s1", "high", True)

    assert level == "high"


def test_a_calm_turn_after_an_emergency_still_requires_confirmation_to_de_escalate() -> None:
    store = RiskHistoryStore()
    store.step("s1", "high", True)

    level = store.step("s1", "low", False)  # 1st low after the emergency spike

    assert level == "high"

    level = store.step("s1", "low", False)  # 2nd consecutive low -- de-escalates

    assert level == "low"


def test_sessions_are_isolated_from_each_other() -> None:
    store = RiskHistoryStore()
    store.step("s1", "high", True)

    level = store.step("s2", "low", False)

    assert level == "low"


def test_clear_session_resets_state() -> None:
    store = RiskHistoryStore()
    store.step("s1", "high", True)

    store.clear_session("s1")
    level = store.step("s1", "low", False)

    assert level == "low"
