import { useCallback, useState } from "react";

export type SpeakerRole = "doctor" | "patient" | "unassigned";

/**
 * Maps diarization's content-neutral labels ("speaker_a"/"speaker_b") to a
 * clinical role. Diarization can tell voices apart but not which one is the
 * doctor -- this mapping is a human-in-the-loop UI action (Blueprint
 * Section 1 Principle 4: AI never overwrites the human-readable transcript),
 * kept in client state only. Not yet persisted to the server -- that's
 * orchestrator/session-state territory (Phase 4+).
 */
export function useSpeakerRoles() {
  const [roles, setRoles] = useState<Record<string, SpeakerRole>>({});

  const assignRole = useCallback((speakerLabel: string, role: SpeakerRole) => {
    setRoles((prev) => ({ ...prev, [speakerLabel]: role }));
  }, []);

  const roleFor = useCallback((speakerLabel: string): SpeakerRole => roles[speakerLabel] ?? "unassigned", [roles]);

  return { roleFor, assignRole };
}
