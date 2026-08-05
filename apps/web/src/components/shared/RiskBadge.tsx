import type { RiskLevel } from "@medibridge/shared-types";
import { useTheme } from "../../theme/ThemeProvider";

const LEVEL_LABEL: Record<RiskLevel, string> = {
  low: "Low risk",
  medium: "Medium risk",
  high: "High risk",
};

export interface RiskBadgeProps {
  level: RiskLevel;
  reason: string;
}

/** Risk-level badge (Blueprint Section 2.2: "Low/Medium/High classifier
 * ... always shown with the rule or model reason that triggered it --
 * never a bare label"). Reuses the same green/yellow/red traffic-light
 * colors as ConfidenceBadge -- same semantic meaning, no new color
 * vocabulary needed. `reason` is always rendered inline, not hidden behind
 * a tooltip, since risk level is a higher-stakes signal than confidence. */
export function RiskBadge({ level, reason }: RiskBadgeProps) {
  const { colors } = useTheme();
  const color = level === "high" ? colors.danger : level === "medium" ? colors.warning : colors.success;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 4,
          padding: "1px 6px",
          borderRadius: 4,
          border: `1px solid ${color}`,
          color,
          fontSize: 12,
          fontWeight: 600,
          width: "fit-content",
        }}
      >
        {LEVEL_LABEL[level]}
      </span>
      <span style={{ fontSize: 11, color: colors.textSecondary }}>{reason}</span>
    </div>
  );
}
