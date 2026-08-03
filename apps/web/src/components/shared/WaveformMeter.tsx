import { useTheme } from "../../theme/ThemeProvider";

// Fixed per-bar multipliers give the meter visual variety instead of all
// bars moving in lockstep, without needing an animation-frame loop -- the
// meter already re-renders on every onLevel update (~every 256ms).
const BAR_MULTIPLIERS = [0.5, 0.8, 1, 0.65, 0.9, 0.55, 1, 0.7];

export interface WaveformMeterProps {
  level: number;
  label: string;
  active: boolean;
}

/** Live per-speaker audio level meter (Blueprint Section 2.4: "waveform
 * animations (per speaker)"). A bar-meter rather than a literal scrolling
 * waveform -- conveys "audio is flowing and how loud" without needing a
 * canvas-based renderer, matching Phase 3's "no UI polish" scope. */
export function WaveformMeter({ level, label, active }: WaveformMeterProps) {
  const { colors } = useTheme();
  const clampedLevel = Math.max(0, Math.min(1, level));

  return (
    <div aria-label={`${label} audio level`} role="img" style={{ display: "flex", alignItems: "flex-end", gap: 2 }}>
      {BAR_MULTIPLIERS.map((multiplier, index) => {
        const heightPct = active ? Math.max(0.08, clampedLevel * multiplier) : 0.08;
        return (
          <div
            key={index}
            style={{
              width: 4,
              height: 24,
              background: colors.border,
              position: "relative",
              overflow: "hidden",
              borderRadius: 2,
            }}
          >
            <div
              style={{
                position: "absolute",
                bottom: 0,
                width: "100%",
                height: `${heightPct * 100}%`,
                background: active ? colors.primary : colors.border,
                transition: "height 120ms ease-out",
              }}
            />
          </div>
        );
      })}
    </div>
  );
}
