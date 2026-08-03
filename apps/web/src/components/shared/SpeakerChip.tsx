import { useTheme } from "../../theme/ThemeProvider";
import type { SpeakerRole } from "../../hooks/useSpeakerRoles";

const ROLE_LABEL: Record<SpeakerRole, string> = {
  doctor: "Doctor",
  patient: "Patient",
  unassigned: "Unassigned",
};

export interface SpeakerChipProps {
  speakerLabel: string;
  confidence: number;
  role: SpeakerRole;
  onAssignRole: (role: SpeakerRole) => void;
}

/** Color-coded speaker chip + role assignment (Blueprint Section 2.1:
 * "Speaker diarization ... color-coded, confidence-scored"). The label
 * itself ("speaker_a"/"speaker_b") is content-neutral; role assignment is
 * an explicit clinician action, never inferred (Section 1 Principle 4). */
export function SpeakerChip({ speakerLabel, confidence, role, onAssignRole }: SpeakerChipProps) {
  const { colors } = useTheme();
  const dotColor = speakerLabel === "speaker_a" ? colors.speakerA : colors.speakerB;
  const confidencePct = Math.round(confidence * 100);

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
      <span
        aria-hidden="true"
        style={{ width: 8, height: 8, borderRadius: "50%", background: dotColor, display: "inline-block" }}
      />
      <span style={{ color: colors.textSecondary }}>
        {ROLE_LABEL[role]} ({confidencePct}% confidence)
      </span>
      <label>
        <span className="sr-only" style={{ position: "absolute", left: -9999 }}>
          Assign role for {speakerLabel}
        </span>
        <select
          value={role}
          onChange={(event) => onAssignRole(event.target.value as SpeakerRole)}
          aria-label={`Assign role for ${speakerLabel}`}
        >
          <option value="unassigned">Unassigned</option>
          <option value="doctor">Doctor</option>
          <option value="patient">Patient</option>
        </select>
      </label>
    </div>
  );
}
