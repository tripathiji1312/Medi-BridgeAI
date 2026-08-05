import type { CSSProperties } from "react";
import type { TranscriptEvent } from "@medibridge/shared-types";
import { useTheme } from "../../theme/ThemeProvider";
import { computeSessionAnalytics } from "../../utils/analytics";
import { formatMsAsTimestamp } from "../../utils/time";

export interface AnalyticsDashboardProps {
  finals: TranscriptEvent[];
}

/** Analytics Dashboard (Blueprint Section 2.4: "consultation time, speaking
 * ratio, symptom count, avg confidence, emotion trend, accuracy stats").
 * Computed entirely client-side from events already held in memory for the
 * live transcript -- no new backend storage needed for a purely derived
 * view. See utils/analytics.ts for the honest interpretation notes on
 * "consultation time" (audio-spanned, not wall-clock) and "accuracy
 * stats" (ASR self-confidence, since there's no ground truth to measure
 * real accuracy against). */
export function AnalyticsDashboard({ finals }: AnalyticsDashboardProps) {
  const { colors } = useTheme();
  const analytics = computeSessionAnalytics(finals);

  if (finals.length === 0) {
    return (
      <section aria-label="Analytics dashboard">
        <h2 style={{ fontSize: 14 }}>Analytics</h2>
        <p style={{ color: colors.textSecondary, fontSize: 12 }}>No data yet.</p>
      </section>
    );
  }

  const tileStyle: CSSProperties = {
    border: `1px solid ${colors.border}`,
    borderRadius: 6,
    padding: 8,
    fontSize: 12,
  };

  return (
    <section aria-label="Analytics dashboard">
      <h2 style={{ fontSize: 14 }}>Analytics</h2>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 8 }}>
        <div style={tileStyle}>
          <div style={{ color: colors.textSecondary }}>Consultation time</div>
          <div>{formatMsAsTimestamp(analytics.consultationDurationMs)}</div>
        </div>

        <div style={tileStyle}>
          <div style={{ color: colors.textSecondary }}>Symptom count</div>
          <div>{analytics.symptomCount}</div>
        </div>

        <div style={tileStyle}>
          <div style={{ color: colors.textSecondary }}>Avg confidence</div>
          <div>
            {analytics.avgConfidenceV2 !== null ? `${Math.round(analytics.avgConfidenceV2 * 100)}%` : "n/a"}
          </div>
        </div>

        <div style={tileStyle}>
          <div style={{ color: colors.textSecondary }}>ASR self-confidence (avg)</div>
          <div>{analytics.avgAsrConfidence !== null ? `${Math.round(analytics.avgAsrConfidence * 100)}%` : "n/a"}</div>
        </div>

        {Object.keys(analytics.speakingRatio).length > 0 && (
          <div style={tileStyle}>
            <div style={{ color: colors.textSecondary }}>Speaking ratio</div>
            {Object.entries(analytics.speakingRatio).map(([label, ratio]) => (
              <div key={label}>
                {label}: {Math.round(ratio * 100)}%
              </div>
            ))}
          </div>
        )}

        {Object.keys(analytics.emotionTrend).length > 0 && (
          <div style={tileStyle}>
            <div style={{ color: colors.textSecondary }}>Emotion trend</div>
            {Object.entries(analytics.emotionTrend).map(([label, count]) => (
              <div key={label}>
                {label}: {count}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
