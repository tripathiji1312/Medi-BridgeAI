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

/** Mirrors services/speech-pipeline/app/asr/schemas.py TranscriptEvent --
 * the message shape sent over gateway's /ws/transcribe (proxied verbatim
 * from speech-pipeline, per AGENT_INSTRUCTIONS.md Section 2 gateway
 * boundary: routing only, no reinterpretation). */
export interface TranscriptEvent {
  type: "partial" | "final" | "error";
  utterance_id: string;
  segment: TranscriptSegment | null;
  error: string | null;
  latency_ms: number | null;
}
