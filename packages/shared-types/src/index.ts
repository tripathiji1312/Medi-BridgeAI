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
