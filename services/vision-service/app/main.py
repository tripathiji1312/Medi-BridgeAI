from fastapi import FastAPI

from app.health import HealthResponse

SERVICE_NAME = "vision-service"
SERVICE_VERSION = "0.1.0"

app = FastAPI(title=SERVICE_NAME)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=SERVICE_NAME, version=SERVICE_VERSION)
