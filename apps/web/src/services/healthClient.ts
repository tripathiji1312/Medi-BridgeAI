import type { HealthResponse } from "@medibridge/shared-types";

/**
 * Fetches gateway health. Never throws on a degraded/unreachable gateway —
 * callers must be able to render a "degraded" state rather than crash
 * (Blueprint Section 6.1: no single service outage may crash the session).
 */
export async function fetchGatewayHealth(
  baseUrl: string,
  fetchImpl: typeof fetch = fetch,
): Promise<HealthResponse> {
  try {
    const res = await fetchImpl(`${baseUrl}/health`);
    if (!res.ok) {
      return { status: "degraded", service: "gateway", version: "unknown" };
    }
    const data = (await res.json()) as HealthResponse;
    return data;
  } catch {
    return { status: "down", service: "gateway", version: "unknown" };
  }
}
