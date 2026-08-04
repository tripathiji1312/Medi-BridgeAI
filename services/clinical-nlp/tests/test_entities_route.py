from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.entities import create_entities_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(create_entities_router())
    return TestClient(app)


def test_extract_endpoint_returns_entities_with_lexicon_version() -> None:
    client = _client()

    response = client.post("/entities/extract", json={"text": "मुझे बुखार है", "language": "hi"})

    assert response.status_code == 200
    body = response.json()
    assert body["lexicon_version"]
    assert any(e["canonical_name"] == "fever" for e in body["entities"])


def test_extract_endpoint_returns_empty_list_for_text_with_no_medical_terms() -> None:
    client = _client()

    response = client.post("/entities/extract", json={"text": "hello, how are you", "language": "en"})

    assert response.status_code == 200
    assert response.json()["entities"] == []


def test_every_returned_entity_has_a_span_that_matches_its_own_text() -> None:
    client = _client()
    text = "I have chest pain and a cough"

    response = client.post("/entities/extract", json={"text": text, "language": "en"})

    body = response.json()
    assert len(body["entities"]) >= 1
    for entity in body["entities"]:
        assert text[entity["start_char"] : entity["end_char"]] == entity["text"]
