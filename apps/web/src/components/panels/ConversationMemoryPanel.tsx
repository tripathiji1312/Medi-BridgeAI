import type { SessionMemory } from "../../hooks/useConversationMemory";
import { useTheme } from "../../theme/ThemeProvider";

export interface ConversationMemoryPanelProps {
  sessionId: string | null;
  memory: SessionMemory | null;
  error: string | null;
  removeCaseMemoryEntry: (entryId: string) => void | Promise<void>;
}

/** "Conversation Memory Status" panel (Blueprint Section 2.4): what
 * context the AI is currently tracking, as explicit chips the clinician
 * can remove. Case-memory entries are populated by Phase 5's symptom/
 * medication/allergy extraction -- this panel and its remove action work
 * today, but the chip list will be empty until that phase wires
 * extraction into orchestrator's case-memory API.
 *
 * Purely presentational -- data comes from LiveTranscriptPanel's single
 * useConversationMemory() call, shared with SummaryPanel/TimelineView so
 * the same session-memory fetch isn't triggered three times over. */
export function ConversationMemoryPanel({ sessionId, memory, error, removeCaseMemoryEntry }: ConversationMemoryPanelProps) {
  const { colors } = useTheme();

  if (!sessionId) {
    return (
      <section aria-label="Conversation memory">
        <h2 style={{ fontSize: 14 }}>Conversation Memory</h2>
        <p style={{ color: colors.textSecondary, fontSize: 12 }}>Not tracking -- no active session.</p>
      </section>
    );
  }

  return (
    <section aria-label="Conversation memory">
      <h2 style={{ fontSize: 14 }}>Conversation Memory</h2>

      {error && (
        <p role="alert" style={{ color: colors.warning, fontSize: 12 }}>
          {error}
        </p>
      )}

      {memory && (
        <>
          <p style={{ color: colors.textSecondary, fontSize: 12 }}>
            Tracking {memory.utterances.length} utterance{memory.utterances.length === 1 ? "" : "s"}
          </p>

          <ul aria-label="Case memory" style={{ display: "flex", flexWrap: "wrap", gap: 6, listStyle: "none", padding: 0 }}>
            {memory.case_memory.map((entry) => (
              <li
                key={entry.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  border: `1px solid ${colors.border}`,
                  borderRadius: 12,
                  padding: "2px 8px",
                  fontSize: 12,
                }}
              >
                <span style={{ color: colors.textSecondary }}>{entry.category}:</span>
                <span>{entry.value}</span>
                <button
                  aria-label={`Remove ${entry.category} ${entry.value} from memory`}
                  onClick={() => void removeCaseMemoryEntry(entry.id)}
                  style={{ border: "none", background: "none", cursor: "pointer", color: colors.textSecondary }}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
          {memory.case_memory.length === 0 && (
            <p style={{ color: colors.textSecondary, fontSize: 12 }}>
              No symptoms, medications, or allergies tracked yet.
            </p>
          )}
        </>
      )}
    </section>
  );
}
