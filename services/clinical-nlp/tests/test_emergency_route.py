from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.emergency import create_emergency_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(create_emergency_router())
    return TestClient(app)


def test_emergency_phrase_triggers_an_alert_with_a_named_reason() -> None:
    client = _client()

    response = client.post("/emergency/detect", json={"text": "I have severe chest pain", "language": "en"})

    assert response.status_code == 200
    body = response.json()
    assert body["alert"] is True
    assert body["reason"] is not None
    assert "chest pain" in body["reason"]
    assert len(body["matches"]) >= 1


def test_routine_text_does_not_trigger_an_alert() -> None:
    client = _client()

    response = client.post("/emergency/detect", json={"text": "I have a mild headache", "language": "en"})

    assert response.status_code == 200
    body = response.json()
    assert body["alert"] is False
    assert body["reason"] is None
    assert body["matches"] == []


def test_fast_stroke_criteria_phrase_triggers_an_alert() -> None:
    client = _client()

    response = client.post(
        "/emergency/detect", json={"text": "his speech is slurred and his face is drooping", "language": "en"}
    )

    body = response.json()
    assert body["alert"] is True
    names = {m["canonical_name"] for m in body["matches"]}
    assert "slurred speech" in names
    assert "facial drooping" in names


def test_response_always_carries_the_lexicon_version() -> None:
    client = _client()

    response = client.post("/emergency/detect", json={"text": "anything", "language": "en"})

    assert response.json()["lexicon_version"]
