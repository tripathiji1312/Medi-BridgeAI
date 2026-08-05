import pytest

from app.memory.schemas import AddCaseMemoryEntryRequest, AddDismissedAlertRequest, AppendUtteranceRequest
from app.memory.store import CaseMemoryEntryNotFoundError, MemoryStore, SessionNotFoundError


def test_appending_an_utterance_creates_the_session_implicitly() -> None:
    store = MemoryStore()

    utterance = store.append_utterance(
        "session-1", AppendUtteranceRequest(speaker="speaker_a", original_text="मुझे बुखार है")
    )

    assert utterance.original_text == "मुझे बुखार है"
    assert utterance.sequence == 0
    memory = store.get_memory("session-1")
    assert len(memory.utterances) == 1


def test_utterances_are_ordered_and_sequence_numbered() -> None:
    store = MemoryStore()
    store.append_utterance("s1", AppendUtteranceRequest(original_text="first"))
    store.append_utterance("s1", AppendUtteranceRequest(original_text="second"))

    memory = store.get_memory("s1")

    assert [u.original_text for u in memory.utterances] == ["first", "second"]
    assert [u.sequence for u in memory.utterances] == [0, 1]


def test_sessions_are_isolated_from_each_other() -> None:
    store = MemoryStore()
    store.append_utterance("session-a", AppendUtteranceRequest(original_text="a's utterance"))
    store.append_utterance("session-b", AppendUtteranceRequest(original_text="b's utterance"))

    assert len(store.get_memory("session-a").utterances) == 1
    assert len(store.get_memory("session-b").utterances) == 1
    assert store.get_memory("session-a").utterances[0].original_text == "a's utterance"


def test_get_memory_raises_for_an_unknown_session_rather_than_returning_empty() -> None:
    store = MemoryStore()

    with pytest.raises(SessionNotFoundError):
        store.get_memory("never-created")


def test_case_memory_entries_can_be_added_and_removed() -> None:
    store = MemoryStore()
    store.append_utterance("s1", AppendUtteranceRequest(original_text="मुझे बुखार है"))
    entry = store.add_case_memory_entry(
        "s1", AddCaseMemoryEntryRequest(category="symptom", value="fever")
    )

    assert store.get_memory("s1").case_memory == [entry]

    store.remove_case_memory_entry("s1", entry.id)

    assert store.get_memory("s1").case_memory == []


def test_removing_an_unknown_case_memory_entry_raises_rather_than_silently_no_opping() -> None:
    store = MemoryStore()
    store.append_utterance("s1", AppendUtteranceRequest(original_text="x"))

    with pytest.raises(CaseMemoryEntryNotFoundError):
        store.remove_case_memory_entry("s1", "does-not-exist")


def test_dismissed_alerts_can_be_added_and_carry_a_reason_and_source() -> None:
    store = MemoryStore()
    store.append_utterance("s1", AppendUtteranceRequest(original_text="chest pain"))
    utterance_id = store.get_memory("s1").utterances[0].id

    entry = store.add_dismissed_alert(
        "s1", AddDismissedAlertRequest(reason="Patient clarified: no chest pain, mistranslation", source_utterance_id=utterance_id)
    )

    assert entry.reason == "Patient clarified: no chest pain, mistranslation"
    assert entry.source_utterance_id == utterance_id
    assert store.get_memory("s1").dismissed_alerts == [entry]


def test_dismissed_alerts_are_isolated_per_session() -> None:
    store = MemoryStore()
    store.append_utterance("s1", AppendUtteranceRequest(original_text="x"))
    store.append_utterance("s2", AppendUtteranceRequest(original_text="y"))

    store.add_dismissed_alert("s1", AddDismissedAlertRequest(reason="false positive"))

    assert len(store.get_memory("s1").dismissed_alerts) == 1
    assert len(store.get_memory("s2").dismissed_alerts) == 0


def test_clear_session_removes_all_memory_for_that_session_only() -> None:
    store = MemoryStore()
    store.append_utterance("s1", AppendUtteranceRequest(original_text="x"))
    store.append_utterance("s2", AppendUtteranceRequest(original_text="y"))

    store.clear_session("s1")

    with pytest.raises(SessionNotFoundError):
        store.get_memory("s1")
    assert len(store.get_memory("s2").utterances) == 1
