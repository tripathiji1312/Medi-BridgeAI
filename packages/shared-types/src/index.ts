// Shared contracts between apps/web, services/gateway, and (mirrored by hand) the
// Python services' pydantic models. Grows one contract per phase — do not pre-add
// contracts for features not yet built (Blueprint Section 6.2 vertical-slice rule).

export type ServiceStatus = "ok" | "degraded" | "down";

/** Contract for every service's GET /health endpoint. */
export interface HealthResponse {
  status: ServiceStatus;
  service: string;
  version: string;
}

/** Mirrors services/speech-pipeline/app/asr/schemas.py TranscriptSegment. */
export interface TranscriptSegment {
  text: string;
  is_final: boolean;
  confidence: number;
  start_ms: number;
  end_ms: number;
  language: string;
}

/** Mirrors services/speech-pipeline/app/mt/schemas.py TranslationSegment. */
export interface TranslationSegment {
  text: string;
  source_language: string;
  target_language: string;
}

/** Mirrors services/speech-pipeline/app/tts/schemas.py TTSAudioSegment. */
export interface TTSAudioSegment {
  audio_base64: string;
  sample_rate: number;
  format: string;
}

/** Mirrors services/speech-pipeline/app/diarization/schemas.py
 * SpeakerAssignment. `speaker_label` is content-neutral ("speaker_a" /
 * "speaker_b") -- diarization can tell voices apart but not which one is
 * the doctor; mapping a label to a clinical role is a human-in-the-loop UI
 * action (Blueprint Section 1 Principle 4), handled client-side. */
export interface SpeakerAssignment {
  speaker_label: string;
  confidence: number;
}

/** Mirrors services/clinical-nlp/app/miscommunication/schemas.py
 * MiscommunicationResult (also mirrored, in turn, by
 * services/speech-pipeline/app/clinical_nlp/schemas.py on the Python side). */
export interface MiscommunicationResult {
  consistent: boolean;
  similarity_score: number;
  negation_flip_detected: boolean;
  reason: string;
}

export type ConfidenceBand = "green" | "yellow" | "red";

/** Mirrors services/speech-pipeline/app/asr/schemas.py TranscriptEvent --
 * the message shape sent over gateway's /ws/transcribe (proxied verbatim
 * from speech-pipeline, per AGENT_INSTRUCTIONS.md Section 2 gateway
 * boundary: routing only, no reinterpretation). */
export interface TranscriptEvent {
  type: "partial" | "final" | "error";
  utterance_id: string;
  // Set once per WebSocket connection (Blueprint Section 2.2) -- lets the
  // client query orchestrator's conversation-memory API for this session.
  session_id: string;
  segment: TranscriptSegment | null;
  error: string | null;
  latency_ms: number | null;
  // Phase 2/3/4: only populated on final events. Each stage's failure is
  // independent and never drops what earlier stages already computed -- the
  // raw Hindi text + confidence is always available even in fully degraded
  // mode (Blueprint Section 7.2).
  translation: TranslationSegment | null;
  translation_error: string | null;
  tts: TTSAudioSegment | null;
  tts_error: string | null;
  speaker: SpeakerAssignment | null;
  speaker_error: string | null;
  back_translation: TranslationSegment | null;
  back_translation_error: string | null;
  miscommunication: MiscommunicationResult | null;
  miscommunication_error: string | null;
  confidence_v2: number | null;
  confidence_band: ConfidenceBand | null;
}
