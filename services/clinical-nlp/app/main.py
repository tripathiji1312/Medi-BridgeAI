from fastapi import FastAPI

from app.health import HealthResponse
from app.miscommunication.provider_factory import get_similarity_provider
from app.routes.miscommunication import create_miscommunication_router

SERVICE_NAME = "clinical-nlp"
SERVICE_VERSION = "0.1.0"

app = FastAPI(title=SERVICE_NAME)
app.include_router(create_miscommunication_router(get_similarity_provider))


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=SERVICE_NAME, version=SERVICE_VERSION)
