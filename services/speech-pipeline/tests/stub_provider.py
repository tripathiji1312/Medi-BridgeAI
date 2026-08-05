"""Test-only ASR provider stub: returns a fixed segment for any input and
records every call so tests can assert on buffer durations/ordering without
needing exact byte-for-byte digest matches (which would be brittle given the
VAD's internal frame-buffering). Distinct from app.asr.fixture_provider,
which is digest-keyed and used for single-call unit tests.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field

from app.asr.schemas import TranscriptSegment
from app.clinical_nlp.schemas import (
    EmergencyDetectionResult,
    MedicalEntity,
    MiscommunicationResult,
    RiskAssessment,
    RiskLevel,
)
from app.emotion.schemas import EmotionAssessment, EmotionCategory
from app.mt.schemas import TranslationSegment
from app.tts.schemas import TTSAudioSegment


@dataclass
class RecordingStubASRProvider:
    text: str = "test transcript"
    confidence: float = 0.9
    language: str = "hi"
    calls: list[bytes] = field(default_factory=list)

    def transcribe(self, pcm16_mono: bytes, sample_rate: int) -> list[TranscriptSegment]:
        self.calls.append(pcm16_mono)
        return [
            TranscriptSegment(
                text=self.text,
                is_final=True,
                confidence=self.confidence,
                start_ms=0,
                end_ms=int(len(pcm16_mono) / 2 / sample_rate * 1000),
                language=self.language,
            )
        ]


@dataclass
class RecordingStubMTProvider:
    translated_text: str = "stub translation"
    calls: list[str] = field(default_factory=list)
    should_fail: bool = False

    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationSegment:
        self.calls.append(text)
        if self.should_fail:
            raise RuntimeError("MT provider unavailable")
        return TranslationSegment(
            text=self.translated_text, source_language=source_lang, target_language=target_lang
        )


@dataclass
class RecordingStubTTSProvider:
    audio: bytes = b"\x01\x02\x03\x04"
    sample_rate: int = 16_000
    calls: list[str] = field(default_factory=list)
    should_fail: bool = False

    def synthesize(self, text: str, language: str) -> TTSAudioSegment:
        self.calls.append(text)
        if self.should_fail:
            raise RuntimeError("TTS provider unavailable")
        return TTSAudioSegment(
            audio_base64=base64.b64encode(self.audio).decode("ascii"),
            sample_rate=self.sample_rate,
            format="pcm16",
        )


@dataclass
class RecordingStubEmbeddingProvider:
    """Returns a fixed embedding for every call regardless of audio content
    -- route-level tests care about the diarizer being invoked and wired
    correctly, not about real clustering (that's app.diarization.diarizer's
    own unit tests, using FixtureEmbeddingProvider for distinct vectors)."""

    embedding: list[float] = field(default_factory=lambda: [1.0, 0.0, 0.0])
    calls: list[bytes] = field(default_factory=list)

    def embed(self, pcm16_mono: bytes, sample_rate: int) -> list[float]:
        self.calls.append(pcm16_mono)
        return self.embedding


@dataclass
class RecordingStubMiscommunicationChecker:
    consistent: bool = True
    similarity_score: float = 0.9
    negation_flip_detected: bool = False
    reason: str = "stub reason"
    calls: list[tuple[str, str]] = field(default_factory=list)
    should_fail: bool = False

    async def check(self, original_text: str, back_translated_text: str, language: str) -> MiscommunicationResult:
        self.calls.append((original_text, back_translated_text))
        if self.should_fail:
            raise RuntimeError("clinical-nlp unavailable")
        return MiscommunicationResult(
            consistent=self.consistent,
            similarity_score=self.similarity_score,
            negation_flip_detected=self.negation_flip_detected,
            reason=self.reason,
        )


@dataclass
class RecordingStubOrchestratorClient:
    calls: list[tuple[str, str | None, str, str | None]] = field(default_factory=list)
    should_fail: bool = False
    timeline_calls: list[tuple[str, str, str, str | None]] = field(default_factory=list)
    timeline_should_fail: bool = False

    async def post_utterance(
        self, session_id: str, speaker: str | None, original_text: str, translated_text: str | None
    ) -> None:
        if self.should_fail:
            raise RuntimeError("orchestrator unavailable")
        self.calls.append((session_id, speaker, original_text, translated_text))

    async def post_timeline_event(
        self,
        session_id: str,
        event_type: str,
        description: str,
        source_utterance_id: str | None,
    ) -> None:
        if self.timeline_should_fail:
            raise RuntimeError("orchestrator unavailable")
        self.timeline_calls.append((session_id, event_type, description, source_utterance_id))


@dataclass
class RecordingStubEntityExtractor:
    entities: list[MedicalEntity] = field(
        default_factory=lambda: [
            MedicalEntity(
                text="stub entity",
                category="symptom",
                canonical_name="stub symptom",
                canonical_code="R00.0",
                definition="a stub entity for tests",
                confidence=1.0,
                start_char=0,
                end_char=11,
                is_fuzzy_match=False,
            )
        ]
    )
    calls: list[tuple[str, str]] = field(default_factory=list)
    should_fail: bool = False

    async def extract(self, text: str, language: str) -> list[MedicalEntity]:
        self.calls.append((text, language))
        if self.should_fail:
            raise RuntimeError("clinical-nlp unavailable")
        return self.entities


@dataclass
class RecordingStubEmergencyDetector:
    alert: bool = False
    matches: list[MedicalEntity] = field(default_factory=list)
    reason: str | None = None
    calls: list[tuple[str, str]] = field(default_factory=list)
    should_fail: bool = False

    async def detect(self, text: str, language: str) -> EmergencyDetectionResult:
        self.calls.append((text, language))
        if self.should_fail:
            raise RuntimeError("clinical-nlp unavailable")
        return EmergencyDetectionResult(
            alert=self.alert, matches=self.matches, reason=self.reason, lexicon_version="stub"
        )


@dataclass
class RecordingStubEmotionClassifier:
    label: EmotionCategory = "neutral"
    confidence: float = 0.5
    reason: str = "stub reason"
    calls: list[bytes] = field(default_factory=list)
    should_fail: bool = False

    def classify(self, pcm16_mono: bytes, sample_rate: int) -> EmotionAssessment:
        self.calls.append(pcm16_mono)
        if self.should_fail:
            raise RuntimeError("emotion classifier unavailable")
        return EmotionAssessment(label=self.label, confidence=self.confidence, reason=self.reason)


@dataclass
class RecordingStubRiskScorer:
    level: RiskLevel = "low"
    raw_level: RiskLevel = "low"
    reason: str = "stub reason"
    emergency_triggered: bool = False
    symptom_count: int = 0
    calls: list[tuple[str, str, str | None, float | None]] = field(default_factory=list)
    should_fail: bool = False

    async def score(
        self,
        session_id: str,
        text: str,
        language: str,
        emotion_label: EmotionCategory | None,
        emotion_confidence: float | None,
    ) -> RiskAssessment:
        self.calls.append((session_id, text, emotion_label, emotion_confidence))
        if self.should_fail:
            raise RuntimeError("clinical-nlp unavailable")
        return RiskAssessment(
            level=self.level,
            raw_level=self.raw_level,
            reason=self.reason,
            emergency_triggered=self.emergency_triggered,
            symptom_count=self.symptom_count,
            lexicon_version="stub",
        )
