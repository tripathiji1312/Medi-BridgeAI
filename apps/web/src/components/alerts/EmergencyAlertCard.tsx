import { useEffect, useRef, useState } from "react";
import { useTheme } from "../../theme/ThemeProvider";

export interface EmergencyAlertCardProps {
  utteranceId: string;
  reason: string;
  /** Called once the clinician submits a dismissal reason. Resolves to
   * whether the dismissal was successfully logged for audit -- a failure
   * still dismisses the banner (never blocks a clinician from clearing a
   * false alarm) but is surfaced separately by the caller. */
  onDismiss: (reason: string) => Promise<boolean>;
  /** Injectable for tests -- real default constructs a Web Audio beep. */
  playAlertSound?: () => void;
}

function defaultPlayAlertSound(): void {
  try {
    const AudioContextImpl = window.AudioContext;
    const ctx = new AudioContextImpl();
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();
    oscillator.type = "sine";
    oscillator.frequency.value = 880;
    gain.gain.value = 0.15;
    oscillator.connect(gain);
    gain.connect(ctx.destination);
    oscillator.start();
    oscillator.stop(ctx.currentTime + 0.4);
    oscillator.onended = () => void ctx.close();
  } catch {
    // Audio isn't available in every environment (headless test runners,
    // browsers without user-gesture-unlocked audio) -- the visible banner
    // is still the primary, always-present alert; sound is a supplement,
    // not the only channel (Blueprint Section 1 Principle 3 still holds
    // via the banner itself).
  }
}

/** Persistent emergency alert banner (Blueprint Section 2.2: "persistent,
 * dismiss-with-reason banner + audible alert"). False-negative-averse by
 * design -- rendered by the caller whenever the server reports an alert,
 * never suppressed client-side. Dismissal always requires a typed reason
 * (never a bare "OK" click) and that reason is sent for audit logging
 * (Blueprint Section 7.3's alarm-fatigue safeguard: dismissals are
 * reviewable, not silently discarded). The audible cue fires once per
 * mount (i.e. once per distinct utteranceId, since the caller keys this
 * component by utterance_id) -- not on every re-render, which would be
 * its own alarm-fatigue problem. */
export function EmergencyAlertCard({
  utteranceId,
  reason,
  onDismiss,
  playAlertSound = defaultPlayAlertSound,
}: EmergencyAlertCardProps) {
  const { colors } = useTheme();
  const [reasonInput, setReasonInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const hasPlayedSound = useRef(false);

  useEffect(() => {
    if (!hasPlayedSound.current) {
      playAlertSound();
      hasPlayedSound.current = true;
    }
  }, [playAlertSound]);

  const handleDismiss = async () => {
    const trimmed = reasonInput.trim();
    if (!trimmed) {
      setValidationError("A reason is required to dismiss an emergency alert.");
      return;
    }
    setSubmitting(true);
    await onDismiss(trimmed);
    setSubmitting(false);
  };

  return (
    <div
      role="alertdialog"
      aria-label="Emergency alert"
      style={{
        border: `2px solid ${colors.danger}`,
        background: colors.surface,
        color: colors.textPrimary,
        borderRadius: 6,
        padding: 12,
        marginBottom: 12,
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span aria-hidden="true" style={{ fontSize: 20 }}>
          🚨
        </span>
        <strong style={{ color: colors.danger }}>Emergency alert</strong>
      </div>
      <p style={{ margin: 0 }}>{reason}</p>
      <p style={{ margin: 0, fontSize: 12, color: colors.textSecondary }}>
        This is an automated keyword match, not a diagnosis. Confirm the situation directly with the patient
        and follow your facility's emergency protocol.
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <label htmlFor={`dismiss-reason-${utteranceId}`} style={{ fontSize: 12 }}>
          Reason for dismissing (required, logged for audit):
        </label>
        <textarea
          id={`dismiss-reason-${utteranceId}`}
          value={reasonInput}
          onChange={(event) => {
            setReasonInput(event.target.value);
            setValidationError(null);
          }}
          rows={2}
        />
        {validationError && (
          <span role="alert" style={{ color: colors.danger, fontSize: 12 }}>
            {validationError}
          </span>
        )}
        <button onClick={() => void handleDismiss()} disabled={submitting}>
          {submitting ? "Dismissing…" : "Dismiss alert"}
        </button>
      </div>
    </div>
  );
}
