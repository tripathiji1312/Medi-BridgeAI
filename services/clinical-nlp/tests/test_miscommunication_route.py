from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.miscommunication.fixture_provider import FixtureSimilarityProvider
from app.routes.miscommunication import create_miscommunication_router


def _build_app(provider: FixtureSimilarityProvider) -> FastAPI:
    app = FastAPI()
    app.include_router(create_miscommunication_router(lambda: provider))
    return app


def test_check_endpoint_returns_a_consistent_result() -> None:
    provider = FixtureSimilarityProvider({("original", "back"): 0.9})
    client = TestClient(_build_app(provider))

    response = client.post(
        "/miscommunication/check",
        json={"original_text": "original", "back_translated_text": "back", "language": "hi"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["consistent"] is True
    assert body["similarity_score"] == 0.9
    assert body["reason"]  # never empty


def test_check_endpoint_returns_503_with_a_reason_when_the_provider_is_unavailable() -> None:
    def unavailable_provider() -> FixtureSimilarityProvider:
        raise RuntimeError("similarity model not installed")

    app = FastAPI()
    app.include_router(create_miscommunication_router(unavailable_provider))
    client = TestClient(app)

    response = client.post(
        "/miscommunication/check",
        json={"original_text": "a", "back_translated_text": "b", "language": "hi"},
    )

    assert response.status_code == 503
    assert "not installed" in response.json()["detail"]
