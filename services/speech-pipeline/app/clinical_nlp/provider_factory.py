"""Factory for the miscommunication checker. Unlike the ML provider
factories, this one isn't lazy-behind-an-import (httpx is always
installed) -- MEDIBRIDGE_FIXTURE_MODE here just points at wherever the
fixture-mode clinical-nlp instance is running instead of swapping the
implementation, since the real implementation *is* just an HTTP call."""

from __future__ import annotations

import os
from functools import lru_cache

from app.clinical_nlp.http_provider import HttpMiscommunicationChecker
from app.clinical_nlp.provider import MiscommunicationChecker


@lru_cache(maxsize=1)
def get_miscommunication_checker() -> MiscommunicationChecker:
    base_url = os.environ.get("CLINICAL_NLP_URL", "http://localhost:8002")
    return HttpMiscommunicationChecker(base_url=base_url)
