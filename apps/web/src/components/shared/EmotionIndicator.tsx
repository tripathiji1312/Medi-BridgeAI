import type { EmotionCategory } from "@medibridge/shared-types";
import { emotionColors } from "@medibridge/design-tokens";
import { useTheme } from "../../theme/ThemeProvider";

const LABEL: Record<EmotionCategory, string> = {
  calm: "Calm",
  anxious: "Anxious",
  fearful: "Fearful",
  stressed: "Stressed",
  angry: "Angry",
  happy: "Happy",
  neutral: "Neutral",
};

export interface EmotionIndicatorProps {
  label: EmotionCategory;
  confidence: number;
  reason: string;
  disclaimer: string;
}

/** Emotion indicator chip (Blueprint Section 2.2: "7-class ... shown per
 * utterance, with an explicit 'estimated from voice tone, not verified'
 * disclaimer"). The disclaimer is always rendered, not just available on
 * hover, since misreading tone (Blueprint Section 7.3: "classifier
 * misreads culturally different expressiveness norms as distress") is a
 * real, documented risk this component exists to guard against. */
export function EmotionIndicator({ label, confidence, reason, disclaimer }: EmotionIndicatorProps) {
  const { mode, colors } = useTheme();
  const color = emotionColors[mode][label] ?? colors.textSecondary;
  const confidencePct = Math.round(confidence * 100);

  return (
    <span
      title={`${reason} ${disclaimer}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        padding: "1px 6px",
        borderRadius: 4,
        border: `1px solid ${color}`,
        color,
        fontSize: 12,
        cursor: "help",
      }}
    >
      Tone: {LABEL[label]} ({confidencePct}%)
    </span>
  );
}
