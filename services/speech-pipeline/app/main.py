from fastapi import FastAPI

from app.asr.provider_factory import get_asr_provider
from app.clinical_nlp.provider_factory import (
    get_emergency_detector,
    get_entity_extractor,
    get_miscommunication_checker,
    get_risk_scorer,
)
from app.diarization.provider_factory import get_embedding_provider
from app.emotion.provider_factory import get_emotion_classifier
from app.health import HealthResponse
from app.mt.provider_factory import get_mt_provider
from app.orchestrator_client_factory import get_orchestrator_client
from app.routes.transcribe_ws import create_transcribe_router
from app.tts.provider_factory import get_tts_provider

SERVICE_NAME = "speech-pipeline"
SERVICE_VERSION = "0.1.0"

app = FastAPI(title=SERVICE_NAME)
app.include_router(
    create_transcribe_router(
        get_asr_provider,
        get_mt_provider,
        get_tts_provider,
        get_embedding_provider,
        get_miscommunication_checker,
        get_orchestrator_client,
        get_entity_extractor,
        get_emergency_detector,
        get_emotion_classifier,
        get_risk_scorer,
    )
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=SERVICE_NAME, version=SERVICE_VERSION)
