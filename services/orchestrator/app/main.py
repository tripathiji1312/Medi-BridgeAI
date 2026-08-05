from fastapi import FastAPI

from app.health import HealthResponse
from app.memory.store import MemoryStore
from app.routes.memory import create_memory_router
from app.summary.client import get_summarizer_client

SERVICE_NAME = "orchestrator"
SERVICE_VERSION = "0.1.0"

app = FastAPI(title=SERVICE_NAME)

_store = MemoryStore()
app.include_router(create_memory_router(lambda: _store, get_summarizer_client))


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=SERVICE_NAME, version=SERVICE_VERSION)
