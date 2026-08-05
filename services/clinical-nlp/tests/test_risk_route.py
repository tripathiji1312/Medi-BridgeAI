from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.risk_scoring.hysteresis import RiskHistoryStore
from app.routes.risk import create_risk_router


def _client(store: RiskHistoryStore | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(create_risk_router(lambda: store or RiskHistoryStore()))
    return TestClient(app)


def test_score_returns_level_and_reason() -> None:
    client = _client()

    response = client.post(
        "/risk/score", json={"session_id": "s1", "text": "I have a mild headache", "language": "en"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["level"] == "low"
    assert body["raw_level"] == "low"
    assert body["reason"]
    assert body["lexicon_version"]


def test_emergency_keyword_scores_high() -> None:
    client = _client()

    response = client.post(
        "/risk/score", json={"session_id": "s1", "text": "I have severe chest pain", "language": "en"}
    )

    body = response.json()
    assert body["level"] == "high"
    assert body["emergency_triggered"] is True


def test_hysteresis_state_persists_across_requests_for_the_same_session() -> None:
    store = RiskHistoryStore()
    client = _client(store)

    client.post("/risk/score", json={"session_id": "s1", "text": "I have a headache", "language": "en"})
    r2 = client.post(
        "/risk/score", json={"session_id": "s1", "text": "I have a headache and a cough", "language": "en"}
    )
    r3 = client.post(
        "/risk/score", json={"session_id": "s1", "text": "I have a headache and a cough", "language": "en"}
    )

    # First medium reading shouldn't flip the displayed level on its own.
    assert r2.json()["raw_level"] == "medium"
    assert r2.json()["level"] == "low"
    # Second consecutive medium reading confirms the escalation.
    assert r3.json()["level"] == "medium"


def test_emotion_signal_is_accepted_and_can_escalate_risk() -> None:
    client = _client()

    response = client.post(
        "/risk/score",
        json={
            "session_id": "s1",
            "text": "I have a headache",
            "language": "en",
            "emotion_label": "anxious",
            "emotion_confidence": 0.9,
        },
    )

    body = response.json()
    assert body["level"] == "medium"
    assert "anxious" in body["reason"]


def test_clear_session_resets_hysteresis() -> None:
    store = RiskHistoryStore()
    client = _client(store)
    client.post("/risk/score", json={"session_id": "s1", "text": "I have severe chest pain", "language": "en"})

    response = client.delete("/risk/sessions/s1")

    assert response.status_code == 204
    r2 = client.post("/risk/score", json={"session_id": "s1", "text": "I have a headache", "language": "en"})
    assert r2.json()["level"] == "low"
