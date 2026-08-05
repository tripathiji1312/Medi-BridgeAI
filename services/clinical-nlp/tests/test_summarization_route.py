from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.summarization import create_summarization_router
from app.summarization.fixture_provider import StaticSummarizer
from app.summarization.provider import Summarizer
from app.summarization.schemas import StructuredSummary, SummaryUtterance


class _FailingSummarizer:
    async def summarize(self, utterances: list[SummaryUtterance]) -> StructuredSummary:
        raise RuntimeError("summarization failed: upstream unavailable")


def _client(summarizer: Summarizer) -> TestClient:
    app = FastAPI()
    app.include_router(create_summarization_router(lambda: summarizer))
    return TestClient(app)


def test_summarize_returns_a_grounded_structured_summary() -> None:
    client = _client(StaticSummarizer())

    response = client.post(
        "/summarize",
        json={
            "utterances": [
                {
                    "utterance_id": "u1",
                    "speaker": "patient",
                    "original_text": "मुझे बुखार है",
                    "translated_text": "I have a fever",
                }
            ]
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["complaints"][0]["source_utterance_id"] == "u1"
    assert body["model_name"] == "static-fixture"
    assert body["discarded_ungrounded_count"] == 0


def test_summarize_returns_503_not_a_silent_empty_summary_on_failure() -> None:
    client = _client(_FailingSummarizer())

    response = client.post("/summarize", json={"utterances": []})

    assert response.status_code == 503
    assert "upstream unavailable" in response.json()["detail"]
