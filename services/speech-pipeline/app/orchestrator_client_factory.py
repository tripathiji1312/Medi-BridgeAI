"""Factory for the orchestrator client. Not lazy-behind-an-import like the
ML provider factories -- httpx is always installed, the real
implementation just makes an HTTP call."""

from __future__ import annotations

import os
from functools import lru_cache

from app.orchestrator_client import HttpOrchestratorClient, OrchestratorClient


@lru_cache(maxsize=1)
def get_orchestrator_client() -> OrchestratorClient:
    base_url = os.environ.get("ORCHESTRATOR_URL", "http://localhost:8004")
    return HttpOrchestratorClient(base_url=base_url)
