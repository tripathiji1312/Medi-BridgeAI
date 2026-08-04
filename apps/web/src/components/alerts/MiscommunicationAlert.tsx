import type { MiscommunicationResult } from "@medibridge/shared-types";
import { useTheme } from "../../theme/ThemeProvider";

export interface MiscommunicationAlertProps {
  result: MiscommunicationResult;
}

/** Inline miscommunication alert (Blueprint Section 2.4: "AI Miscommunication
 * Alerts"). Only rendered by the caller when result.consistent is false --
 * never a bare label, always shows the "why" (Section 1 Principle 2). A
 * panel-level running log across utterances is a documented follow-up
 * (docs/PROGRESS.md), not built here to keep this vertical slice focused. */
export function MiscommunicationAlert({ result }: MiscommunicationAlertProps) {
  const { colors } = useTheme();

  return (
    <div role="alert" style={{ color: colors.danger, fontSize: 12, display: "flex", gap: 6 }}>
      <span aria-hidden="true">⚠</span>
      <span>
        Possible miscommunication{result.negation_flip_detected ? " (negation mismatch)" : ""}: {result.reason}
      </span>
    </div>
  );
}
