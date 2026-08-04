import type { ConfidenceBand } from "@medibridge/shared-types";
import { useTheme } from "../../theme/ThemeProvider";

const BAND_COLOR_KEY: Record<ConfidenceBand, "confidenceGreen" | "confidenceYellow" | "confidenceRed"> = {
  green: "confidenceGreen",
  yellow: "confidenceYellow",
  red: "confidenceRed",
};

export interface ConfidenceBadgeProps {
  score: number;
  band: ConfidenceBand;
}

/** Translation confidence score v2, color-coded per Blueprint Section 2.2
 * (Green >=85, Yellow 60-84, Red <60). Only rendered when both `score` and
 * `band` are present -- LiveTranscriptPanel gates on that, since a
 * composite score without its underlying signals would be fabricated
 * (Section 11.1). */
export function ConfidenceBadge({ score, band }: ConfidenceBadgeProps) {
  const { colors } = useTheme();
  const color = colors[BAND_COLOR_KEY[band]];
  const pct = Math.round(score * 100);

  return (
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
      }}
    >
      Confidence: {pct}%
    </span>
  );
}
