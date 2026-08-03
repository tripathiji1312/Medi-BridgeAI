import { useEffect, useState } from "react";
import type { HealthResponse } from "@medibridge/shared-types";
import { fetchGatewayHealth } from "../../services/healthClient";
import { useTheme } from "../../theme/ThemeProvider";
import { GATEWAY_HTTP_URL } from "../../config";

const STATUS_LABEL: Record<HealthResponse["status"], string> = {
  ok: "All systems operational",
  degraded: "Gateway degraded — some features may be unavailable",
  down: "Gateway unreachable — AI assistance unavailable",
};

/**
 * Model/latency health indicator (Blueprint Section 2.4). Never renders a
 * confident status without a reason — "down"/"degraded" always shows why.
 */
export function HealthStatus() {
  const { colors } = useTheme();
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchGatewayHealth(GATEWAY_HTTP_URL).then((result) => {
      if (!cancelled) setHealth(result);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!health) {
    return <div role="status">Checking gateway status…</div>;
  }

  const color =
    health.status === "ok" ? colors.success : health.status === "degraded" ? colors.warning : colors.danger;

  return (
    <div role="status" style={{ color, fontFamily: "inherit" }} data-status={health.status}>
      {STATUS_LABEL[health.status]}
    </div>
  );
}
