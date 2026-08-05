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

export type EntityCategory = "symptom" | "disease" | "medication" | "allergy" | "vital_sign" | "procedure";

/** Mirrors services/clinical-nlp/app/ner/schemas.py MedicalEntity.
 * `text`/`start_char`/`end_char` are the exact matched substring and its
 * position in whichever text it was extracted from -- grounding via span
 * citation (Blueprint Section 11.1). */
export interface MedicalEntity {
  text: string;
  category: EntityCategory;
  canonical_name: string;
  canonical_code: string | null;
  definition: string;
  confidence: number;
  start_char: number;
  end_char: number;
  is_fuzzy_match: boolean;
}

/** Mirrors services/clinical-nlp/app/emergency_detector/schemas.py
 * EmergencyDetectionResponse. `alert` is never shown bare -- `reason`
 * always names the matched phrase(s) (Blueprint Section 1 Principle 2). */
export interface EmergencyDetectionResult {
  alert: boolean;
  matches: MedicalEntity[];
  reason: string | null;
  lexicon_version: string;
}

/** Mirrors services/speech-pipeline/app/emotion/schemas.py EmotionCategory
 * (Blueprint Section 2.2: "7-class (Calm, Anxious, Fearful, Stressed,
 * Angry, Happy, Neutral)"). */
export type EmotionCategory = "calm" | "anxious" | "fearful" | "stressed" | "angry" | "happy" | "neutral";

/** Mirrors services/speech-pipeline/app/emotion/schemas.py
 * EmotionAssessment. `disclaimer` is always present -- Blueprint Section
 * 2.2's explicit "estimated from voice tone, not verified" requirement. */
export interface EmotionAssessment {
  label: EmotionCategory;
  confidence: number;
  reason: string;
  disclaimer: string;
}

export type RiskLevel = "low" | "medium" | "high";

/** Mirrors services/clinical-nlp/app/risk_scoring/schemas.py
 * RiskAssessment. `level` is the hysteresis-smoothed value to display;
 * `raw_level` is what this single utterance alone would score (Blueprint
 * Section 7.3: smoothing must be auditable, not a black box). */
export interface RiskAssessment {
  level: RiskLevel;
  raw_level: RiskLevel;
  reason: string;
  emergency_triggered: boolean;
  symptom_count: number;
  lexicon_version: string;
}

/** Mirrors services/orchestrator/app/memory/schemas.py DismissedAlert. */
export interface DismissedAlert {
  id: string;
  reason: string;
  source_utterance_id: string | null;
}

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
  // Phase 5 additions. Also final-only, also independently degradable.
  // entities is extracted from the Hindi original; translation_entities
  // from the English translation -- both sides of the bilingual
  // transcript can highlight matched terms independently.
  entities: MedicalEntity[] | null;
  entities_error: string | null;
  translation_entities: MedicalEntity[] | null;
  translation_entities_error: string | null;
  // Phase 6 additions. Also final-only, also independently degradable.
  // emergency is checked first server-side, before translation/anything
  // else, to minimize alert latency (Blueprint Section 3.2 step 10).
  emergency: EmergencyDetectionResult | null;
  emergency_error: string | null;
  emotion: EmotionAssessment | null;
  emotion_error: string | null;
  risk: RiskAssessment | null;
  risk_error: string | null;
}
