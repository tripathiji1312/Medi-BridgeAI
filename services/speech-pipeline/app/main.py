from fastapi import FastAPI

from app.asr.provider_factory import get_asr_provider
from app.health import HealthResponse
from app.routes.transcribe_ws import create_transcribe_router

SERVICE_NAME = "speech-pipeline"
SERVICE_VERSION = "0.1.0"

app = FastAPI(title=SERVICE_NAME)
app.include_router(create_transcribe_router(get_asr_provider))


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=SERVICE_NAME, version=SERVICE_VERSION)
