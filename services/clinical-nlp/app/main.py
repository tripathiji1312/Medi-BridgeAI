from fastapi import FastAPI

from app.health import HealthResponse
from app.miscommunication.provider_factory import get_similarity_provider
from app.risk_scoring.hysteresis import RiskHistoryStore
from app.routes.emergency import create_emergency_router
from app.routes.entities import create_entities_router
from app.routes.miscommunication import create_miscommunication_router
from app.routes.risk import create_risk_router

SERVICE_NAME = "clinical-nlp"
SERVICE_VERSION = "0.1.0"

app = FastAPI(title=SERVICE_NAME)
app.include_router(create_miscommunication_router(get_similarity_provider))
app.include_router(create_entities_router())
app.include_router(create_emergency_router())

_risk_store = RiskHistoryStore()
app.include_router(create_risk_router(lambda: _risk_store))


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=SERVICE_NAME, version=SERVICE_VERSION)
