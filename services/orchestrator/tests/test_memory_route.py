from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.memory.store import MemoryStore
from app.routes.memory import create_memory_router


def _client() -> TestClient:
    store = MemoryStore()
    app = FastAPI()
    app.include_router(create_memory_router(lambda: store))
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


def test_clear_session_then_memory_is_gone() -> None:
    client = _client()
    client.post("/sessions/s1/utterances", json={"original_text": "x"})

    response = client.delete("/sessions/s1")
    assert response.status_code == 204

    assert client.get("/sessions/s1/memory").status_code == 404
