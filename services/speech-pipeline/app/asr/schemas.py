"""Wire schemas for ASR transcript events (Blueprint Section 3.2 step 3).

Every event carries enough to satisfy the "no AI value without a reason"
rule (AGENT_INSTRUCTIONS.md Rule 1): confidence is always present, and
is_final distinguishes a stable result from one that may still change.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.clinical_nlp.schemas import MiscommunicationResult
from app.diarization.schemas import SpeakerAssignment
from app.mt.schemas import TranslationSegment
from app.tts.schemas import TTSAudioSegment


class TranscriptSegment(BaseModel):
    model_config = {"strict": True}

    text: str
    is_final: bool
    confidence: float = Field(ge=0.0, le=1.0)
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    language: str


class TranscriptEvent(BaseModel):
    """Envelope pushed over the /ws/transcribe WebSocket, one per segment
    update. `utterance_id` lets a client correlate a partial with the final
    that supersedes it."""

    model_config = {"strict": True}

    type: str = Field(pattern="^(partial|final|error)$")
    utterance_id: str
    # Set once per WebSocket connection (Blueprint Section 2.2). The client
    # needs this to query orchestrator's conversation-memory API for the
    # "Conversation Memory Status" panel (Section 2.4) -- there's otherwise
    # no way for it to know the session identity speech-pipeline generated.
    session_id: str = "n/a"
    segment: TranscriptSegment | None = None
    error: str | None = None
    # Latency instrumentation (Blueprint Section 8 Phase 1: "Latency
    # instrumentation from day one"; Section 6.1 budget: partials <300ms).
    latency_ms: float | None = None

    # Phase 2 additions. Only populated on final events (Blueprint Section 8
    # Phase 2 scope: MT/TTS run on the finalized transcript, not partials --
    # translating unstable text would waste compute and show flickering
    # output). translation_error/tts_error are populated independently of
    # each other and of `error` above, so a translation-service outage still
    # delivers the raw Hindi transcript (Section 7.2 degraded-mode rule)
    # rather than blocking the whole event.
    translation: TranslationSegment | None = None
    translation_error: str | None = None
    tts: TTSAudioSegment | None = None
    tts_error: str | None = None

    # Phase 3 addition. Also final-only, also independently degradable --
    # a diarization failure never blocks the transcript/translation/TTS
    # already computed (same degrade-not-drop rule as above).
    speaker: SpeakerAssignment | None = None
    speaker_error: str | None = None

    # Phase 4 additions. Also final-only, also independently degradable.
    # back_translation is EN->HI of `translation`, compared against the
    # original `segment.text` by clinical-nlp's miscommunication check
    # (Blueprint Section 3.2 step 6). confidence_v2/confidence_band are
    # only computed when both the ASR confidence and the back-translation
    # similarity are available -- a partial composite would be a fabricated
    # number, not a real one (Section 11.1: no numeric fabrication).
    back_translation: TranslationSegment | None = None
    back_translation_error: str | None = None
    miscommunication: MiscommunicationResult | None = None
    miscommunication_error: str | None = None
    confidence_v2: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_band: str | None = Field(default=None, pattern="^(green|yellow|red)$")
