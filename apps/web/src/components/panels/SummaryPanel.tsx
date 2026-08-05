import type { StructuredSummary, SummaryBullet } from "../../hooks/useConversationMemory";
import { useTheme } from "../../theme/ThemeProvider";

export interface SummaryPanelProps {
  sessionId: string | null;
  summary: StructuredSummary | null;
  approved: boolean;
  error: string | null;
  isGenerating: boolean;
  onGenerate: () => void;
  onApprove: () => void;
}

const SECTION_LABELS: Record<keyof Pick<
  StructuredSummary,
  | "complaints"
  | "symptoms"
  | "objective"
  | "diagnoses_mentioned"
  | "medications"
  | "recommendations"
  | "action_items"
  | "follow_up"
>, string> = {
  complaints: "Complaints",
  symptoms: "Symptoms",
  objective: "Objective",
  diagnoses_mentioned: "Diagnoses Mentioned",
  medications: "Medications",
  recommendations: "Recommendations",
  action_items: "Action Items",
  follow_up: "Follow-up",
};

const SECTION_KEYS = Object.keys(SECTION_LABELS) as (keyof typeof SECTION_LABELS)[];

/** AI Consultation Summary (Blueprint Section 2.4: "draft, clinician must
 * review/approve before export -- never auto-finalized"). Always labeled
 * AI-generated (Blueprint Section 3.3 Principle) -- the DRAFT banner is
 * never removed just because content exists, only once the clinician
 * explicitly approves. Every bullet cites its source utterance id
 * (Blueprint Section 11.1 grounding), and discarded_ungrounded_count is
 * shown, not hidden -- transparency about what the model proposed but
 * couldn't be verified. */
export function SummaryPanel({
  sessionId,
  summary,
  approved,
  error,
  isGenerating,
  onGenerate,
  onApprove,
}: SummaryPanelProps) {
  const { colors } = useTheme();

  if (!sessionId) {
    return (
      <section aria-label="AI consultation summary">
        <h2 style={{ fontSize: 14 }}>AI Consultation Summary</h2>
        <p style={{ color: colors.textSecondary, fontSize: 12 }}>Not tracking -- no active session.</p>
      </section>
    );
  }

  return (
    <section aria-label="AI consultation summary">
      <h2 style={{ fontSize: 14 }}>AI Consultation Summary</h2>

      <button onClick={onGenerate} disabled={isGenerating}>
        {isGenerating ? "Generating…" : summary ? "Regenerate summary" : "Generate summary"}
      </button>

      {error && (
        <p role="alert" style={{ color: colors.warning, fontSize: 12 }}>
          Summary unavailable: {error}
        </p>
      )}

      {summary && (
        <div style={{ border: `1px solid ${colors.border}`, borderRadius: 6, padding: 12, marginTop: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: approved ? colors.success : colors.warning,
                border: `1px solid ${approved ? colors.success : colors.warning}`,
                borderRadius: 4,
                padding: "1px 6px",
              }}
            >
              {approved ? "APPROVED" : "DRAFT — AI-generated, not yet reviewed"}
            </span>
          </div>

          {summary.patient_info && <p style={{ fontSize: 12 }}>{summary.patient_info}</p>}

          {SECTION_KEYS.map((key) => {
            const bullets = summary[key] as SummaryBullet[];
            if (bullets.length === 0) return null;
            return (
              <div key={key} style={{ marginBottom: 8 }}>
                <h3 style={{ fontSize: 12, margin: "0 0 4px" }}>{SECTION_LABELS[key]}</h3>
                <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12 }}>
                  {bullets.map((bullet, index) => (
                    <li key={index} title={`Source: utterance ${bullet.source_utterance_id}`}>
                      {bullet.text}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}

          {summary.discarded_ungrounded_count > 0 && (
            <p style={{ color: colors.textSecondary, fontSize: 11 }}>
              {summary.discarded_ungrounded_count} proposed item
              {summary.discarded_ungrounded_count === 1 ? "" : "s"} could not be grounded in the transcript and{" "}
              {summary.discarded_ungrounded_count === 1 ? "was" : "were"} discarded.
            </p>
          )}

          <p style={{ color: colors.textSecondary, fontSize: 11 }}>Model: {summary.model_name}</p>

          {!approved && (
            <button onClick={onApprove} style={{ marginTop: 4 }}>
              Approve summary
            </button>
          )}
        </div>
      )}
    </section>
  );
}
