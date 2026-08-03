/** Gateway base URLs. Overridable via Vite env vars (VITE_GATEWAY_HTTP_URL/
 * VITE_GATEWAY_WS_URL) so E2E tests and non-default deployments don't need
 * to hardcode localhost:4000 -- previously duplicated as a literal in both
 * HealthStatus and LiveTranscriptPanel with no override mechanism at all. */
export const GATEWAY_HTTP_URL: string = import.meta.env.VITE_GATEWAY_HTTP_URL ?? "http://localhost:4000";

export const GATEWAY_WS_URL: string =
  import.meta.env.VITE_GATEWAY_WS_URL ?? "ws://localhost:4000/ws/transcribe";
