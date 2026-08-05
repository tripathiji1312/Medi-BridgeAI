import type { TimelineEvent, TimelineEventType } from "../../hooks/useConversationMemory";
import { useTheme } from "../../theme/ThemeProvider";
import { formatTimelineTimestamp } from "../../utils/time";

export interface TimelineViewProps {
  sessionId: string | null;
  events: TimelineEvent[];
}

const TYPE_ICON: Record<TimelineEventType, string> = {
  symptom_mentioned: "🩺",
  medication_mentioned: "💊",
  alert_triggered: "🚨",
  alert_dismissed: "✖",
  risk_level_changed: "📈",
};

function downloadJson(filename: string, data: unknown): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

/** Consultation Timeline (Blueprint Section 2.2: "chronological event
 * stream (symptom mentioned, medication mentioned, alert triggered, risk
 * level changed) with timestamps, exportable"). Export here is a plain
 * JSON download -- full PDF/TXT export formatting is Blueprint Section 8's
 * Phase 9 scope ("export (PDF/TXT/JSON)"), not built here. */
export function TimelineView({ sessionId, events }: TimelineViewProps) {
  const { colors } = useTheme();

  if (!sessionId) {
    return (
      <section aria-label="Consultation timeline">
        <h2 style={{ fontSize: 14 }}>Consultation Timeline</h2>
        <p style={{ color: colors.textSecondary, fontSize: 12 }}>Not tracking -- no active session.</p>
      </section>
    );
  }

  return (
    <section aria-label="Consultation timeline">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <h2 style={{ fontSize: 14 }}>Consultation Timeline</h2>
        <button
          onClick={() => downloadJson(`timeline-${sessionId}.json`, events)}
          disabled={events.length === 0}
        >
          Export
        </button>
      </div>

      {events.length === 0 ? (
        <p style={{ color: colors.textSecondary, fontSize: 12 }}>No timeline events yet.</p>
      ) : (
        <ol style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {events.map((event) => (
            <li
              key={event.id}
              style={{ display: "flex", alignItems: "baseline", gap: 8, fontSize: 12, marginBottom: 4 }}
            >
              <span aria-hidden="true">{TYPE_ICON[event.type]}</span>
              <span style={{ color: colors.textSecondary, minWidth: 60 }}>
                {formatTimelineTimestamp(event.timestamp)}
              </span>
              <span>{event.description}</span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
