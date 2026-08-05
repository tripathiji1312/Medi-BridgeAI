from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.memory.schemas import Utterance
from app.memory.store import MemoryStore
from app.routes.memory import create_memory_router
from app.summary.schemas import StructuredSummary, SummaryBullet


class _StubSummarizer:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.received_utterances: list[Utterance] | None = None

    async def summarize(self, utterances: list[Utterance]) -> StructuredSummary:
        self.received_utterances = utterances
        if self.should_fail:
            raise RuntimeError("clinical-nlp unavailable")
        return StructuredSummary(
            patient_info=None,
            complaints=[SummaryBullet(text="fever", source_utterance_id="doesnt-matter")],
            symptoms=[],
            objective=[],
            diagnoses_mentioned=[],
            medications=[],
            recommendations=[],
            action_items=[],
            follow_up=[],
            discarded_ungrounded_count=0,
            model_name="stub",
        )


def _client(summarizer: _StubSummarizer | None = None) -> TestClient:
    store = MemoryStore()
    app = FastAPI()
    app.include_router(create_memory_router(lambda: store, (lambda: summarizer) if summarizer else None))
    return TestClient(app)


def test_append_and_fetch_round_trip() -> None:
    client = _client()

    response = client.post(
        "/sessions/s1/utterances",
        json={"speaker": "speaker_a", "original_text": "मुझे बुखार है", "translated_text": "I have a fever"},
    )
    assert response.status_code == 200
    utterance_id = response.json()["id"]

    memory_response = client.get("/sessions/s1/memory")
    assert memory_response.status_code == 200
    body = memory_response.json()
    assert body["session_id"] == "s1"
    assert len(body["utterances"]) == 1
    assert body["utterances"][0]["id"] == utterance_id


def test_get_memory_for_unknown_session_returns_404_not_an_empty_object() -> None:
    client = _client()

    response = client.get("/sessions/never-created/memory")

    assert response.status_code == 404


def test_case_memory_add_then_remove() -> None:
    client = _client()
    client.post("/sessions/s1/utterances", json={"original_text": "x"})

    add_response = client.post(
        "/sessions/s1/case-memory", json={"category": "symptom", "value": "fever"}
    )
    assert add_response.status_code == 200
    entry_id = add_response.json()["id"]

    memory = client.get("/sessions/s1/memory").json()
    assert len(memory["case_memory"]) == 1

    delete_response = client.delete(f"/sessions/s1/case-memory/{entry_id}")
    assert delete_response.status_code == 204

    memory_after = client.get("/sessions/s1/memory").json()
    assert memory_after["case_memory"] == []


def test_removing_an_unknown_entry_returns_404() -> None:
    client = _client()
    client.post("/sessions/s1/utterances", json={"original_text": "x"})

    response = client.delete("/sessions/s1/case-memory/does-not-exist")

    assert response.status_code == 404


def test_dismissed_alert_add_then_appears_in_memory() -> None:
    client = _client()
    client.post("/sessions/s1/utterances", json={"original_text": "chest pain"})

    response = client.post(
        "/sessions/s1/dismissed-alerts", json={"reason": "false positive, benign chest pressure"}
    )
    assert response.status_code == 200
    assert response.json()["reason"] == "false positive, benign chest pressure"

    memory = client.get("/sessions/s1/memory").json()
    assert len(memory["dismissed_alerts"]) == 1


def test_timeline_event_add_then_appears_in_memory() -> None:
    client = _client()
    client.post("/sessions/s1/utterances", json={"original_text": "fever"})

    response = client.post(
        "/sessions/s1/timeline-events",
        json={"type": "symptom_mentioned", "description": "fever mentioned"},
    )
    assert response.status_code == 200
    assert response.json()["type"] == "symptom_mentioned"

    memory = client.get("/sessions/s1/memory").json()
    assert len(memory["timeline"]) == 1


def test_generate_summary_returns_and_stores_a_draft() -> None:
    client = _client(_StubSummarizer())
    client.post("/sessions/s1/utterances", json={"original_text": "fever"})

    response = client.post("/sessions/s1/summary/generate")

    assert response.status_code == 200
    assert response.json()["model_name"] == "stub"
    memory = client.get("/sessions/s1/memory").json()
    assert memory["draft_summary"]["model_name"] == "stub"
    assert memory["summary_approved"] is False


def test_generate_summary_without_a_configured_summarizer_returns_503() -> None:
    client = _client(None)

    response = client.post("/sessions/s1/summary/generate")

    assert response.status_code == 503


def test_generate_summary_failure_returns_503_not_a_silent_empty_summary() -> None:
    client = _client(_StubSummarizer(should_fail=True))

    response = client.post("/sessions/s1/summary/generate")

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"]


def test_approve_summary_without_a_draft_returns_409() -> None:
    client = _client()
    client.post("/sessions/s1/utterances", json={"original_text": "x"})

    response = client.post("/sessions/s1/summary/approve")

    assert response.status_code == 409


def test_approve_summary_after_generating_succeeds() -> None:
    client = _client(_StubSummarizer())
    client.post("/sessions/s1/utterances", json={"original_text": "fever"})
    client.post("/sessions/s1/summary/generate")

    response = client.post("/sessions/s1/summary/approve")

    assert response.status_code == 204
    memory = client.get("/sessions/s1/memory").json()
    assert memory["summary_approved"] is True


def test_clear_session_then_memory_is_gone() -> None:
    client = _client()
    client.post("/sessions/s1/utterances", json={"original_text": "x"})

    response = client.delete("/sessions/s1")
    assert response.status_code == 204

    assert client.get("/sessions/s1/memory").status_code == 404
