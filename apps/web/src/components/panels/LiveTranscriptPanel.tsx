import { useState } from "react";
import { useLiveTranscript } from "../../hooks/useLiveTranscript";
import { useSpeakerRoles } from "../../hooks/useSpeakerRoles";
import { useDismissAlert } from "../../hooks/useDismissAlert";
import { useConversationMemory } from "../../hooks/useConversationMemory";
import { useTheme } from "../../theme/ThemeProvider";
import { pcm16ToWavDataUrl } from "../../audio/wav";
import { formatMsAsTimestamp } from "../../utils/time";
import { WaveformMeter } from "../shared/WaveformMeter";
import { SpeakerChip } from "../shared/SpeakerChip";
import { ConfidenceBadge } from "../shared/ConfidenceBadge";
import { RiskBadge } from "../shared/RiskBadge";
import { EmotionIndicator } from "../shared/EmotionIndicator";
import { HighlightedText } from "../shared/HighlightedText";
import { MiscommunicationAlert } from "../alerts/MiscommunicationAlert";
import { EmergencyAlertCard } from "../alerts/EmergencyAlertCard";
import { ConversationMemoryPanel } from "./ConversationMemoryPanel";
import { MedicalEntitiesPanel } from "./MedicalEntitiesPanel";
import { SummaryPanel } from "./SummaryPanel";
import { TimelineView } from "./TimelineView";
import { AnalyticsDashboard } from "./AnalyticsDashboard";
import { GATEWAY_WS_URL } from "../../config";
import type { MedicalEntity } from "@medibridge/shared-types";

/** Phase 1-4 scope. Playback uses <audio controls> (no autoplay) so the
 * clinician/patient decides when to hear it -- consistent with
 * "human-in-the-loop always" (Blueprint Section 1). */
export function LiveTranscriptPanel() {
  const { colors } = useTheme();
  const { consentGiven, isActive, events, error, level, start, stop } = useLiveTranscript({
    gatewayWsUrl: GATEWAY_WS_URL,
  });
  const { roleFor, assignRole } = useSpeakerRoles();
  const [dismissedAlertIds, setDismissedAlertIds] = useState<Set<string>>(new Set());

  const finals = events.filter((e) => e.type === "final" && e.segment);
  const latestPartial = [...events].reverse().find((e) => e.type === "partial" && e.segment);
  const latestSessionId = events.length > 0 ? (events[events.length - 1]?.session_id ?? null) : null;
  const sessionId = latestSessionId && latestSessionId !== "n/a" ? latestSessionId : null;
  const allEntities: MedicalEntity[] = finals.flatMap((e) => [
    ...(e.entities ?? []),
    ...(e.translation_entities ?? []),
  ]);
  const { dismiss: dismissAlert, error: dismissAlertError } = useDismissAlert(sessionId);
  const {
    memory,
    error: memoryError,
    removeCaseMemoryEntry,
    generateSummary,
    approveSummary,
    summaryError,
    isGeneratingSummary,
  } = useConversationMemory(sessionId, finals.length);
  // Most recent utterance still carrying an un-dismissed emergency alert --
  // one persistent banner (Blueprint Section 2.2: "persistent ... banner"),
  // not one per matching utterance in the scrolling transcript.
  const activeEmergencyEvent = [...finals]
    .reverse()
    .find((e) => e.emergency?.alert && !dismissedAlertIds.has(e.utterance_id));

  return (
    <section aria-label="Live transcript" style={{ color: colors.textPrimary }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {!consentGiven ? (
          <button onClick={() => void start()}>Start consultation (I consent to audio recording)</button>
        ) : (
          <button onClick={stop}>Stop consultation</button>
        )}
        <WaveformMeter level={level} label="Microphone" active={isActive} />
      </div>

      <p role="status">{isActive ? "Recording" : consentGiven ? "Connecting…" : "Not recording"}</p>

      {error && (
        <p role="alert" style={{ color: colors.danger }}>
          {error}
        </p>
      )}

      {activeEmergencyEvent?.emergency?.reason && (
        <EmergencyAlertCard
          key={activeEmergencyEvent.utterance_id}
          utteranceId={activeEmergencyEvent.utterance_id}
          reason={activeEmergencyEvent.emergency.reason}
          onDismiss={async (reason) => {
            const logged = await dismissAlert(reason, activeEmergencyEvent.utterance_id);
            setDismissedAlertIds((prev) => new Set(prev).add(activeEmergencyEvent.utterance_id));
            return logged;
          }}
        />
      )}
      {dismissAlertError && (
        <p role="alert" style={{ color: colors.warning, fontSize: 12 }}>
          {dismissAlertError}
        </p>
      )}

      <ul aria-live="polite" aria-label="Transcript">
        {finals.map((event) => (
          <li key={event.utterance_id} style={{ marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
              <span style={{ color: colors.textSecondary, fontSize: 12 }}>
                {event.segment && formatMsAsTimestamp(event.segment.start_ms)}–
                {event.segment && formatMsAsTimestamp(event.segment.end_ms)}
              </span>
              {event.speaker && (
                <SpeakerChip
                  speakerLabel={event.speaker.speaker_label}
                  confidence={event.speaker.confidence}
                  role={roleFor(event.speaker.speaker_label)}
                  onAssignRole={(role) => assignRole(event.speaker!.speaker_label, role)}
                />
              )}
              {event.speaker_error && (
                <span role="alert" style={{ color: colors.warning, fontSize: 12 }}>
                  Speaker unknown: {event.speaker_error}
                </span>
              )}
              {event.confidence_v2 !== null && event.confidence_band !== null && (
                <ConfidenceBadge score={event.confidence_v2} band={event.confidence_band} />
              )}
              {event.emotion && (
                <EmotionIndicator
                  label={event.emotion.label}
                  confidence={event.emotion.confidence}
                  reason={event.emotion.reason}
                  disclaimer={event.emotion.disclaimer}
                />
              )}
            </div>
            {event.emotion_error && (
              <div role="alert" style={{ color: colors.warning, fontSize: 12 }}>
                Tone assessment unavailable: {event.emotion_error}
              </div>
            )}
            {event.risk && <RiskBadge level={event.risk.level} reason={event.risk.reason} />}
            {event.risk_error && (
              <div role="alert" style={{ color: colors.warning, fontSize: 12 }}>
                Risk assessment unavailable: {event.risk_error}
              </div>
            )}
            {event.emergency_error && (
              <div role="alert" style={{ color: colors.warning, fontSize: 12 }}>
                Emergency keyword check unavailable: {event.emergency_error}
              </div>
            )}

            <div>
              {event.segment && <HighlightedText text={event.segment.text} entities={event.entities} />}
            </div>
            {event.entities_error && (
              <div role="alert" style={{ color: colors.warning, fontSize: 12 }}>
                Medical term detection unavailable: {event.entities_error}
              </div>
            )}

            {event.translation && (
              <div style={{ color: colors.textSecondary }}>
                <HighlightedText text={event.translation.text} entities={event.translation_entities} />
              </div>
            )}
            {event.translation_entities_error && (
              <div role="alert" style={{ color: colors.warning, fontSize: 12 }}>
                Medical term detection unavailable (translation): {event.translation_entities_error}
              </div>
            )}
            {event.translation_error && (
              <div role="alert" style={{ color: colors.warning }}>
                Translation unavailable: {event.translation_error}
              </div>
            )}

            {event.miscommunication && !event.miscommunication.consistent && (
              <MiscommunicationAlert result={event.miscommunication} />
            )}
            {event.miscommunication_error && (
              <div role="alert" style={{ color: colors.warning, fontSize: 12 }}>
                Miscommunication check unavailable: {event.miscommunication_error}
              </div>
            )}

            {event.tts && (
              <audio controls src={pcm16ToWavDataUrl(event.tts.audio_base64, event.tts.sample_rate)} />
            )}
            {event.tts_error && (
              <div role="alert" style={{ color: colors.warning }}>
                Audio playback unavailable: {event.tts_error}
              </div>
            )}
          </li>
        ))}
        {latestPartial && <li style={{ opacity: 0.6 }}>{latestPartial.segment?.text} …</li>}
      </ul>

      <MedicalEntitiesPanel entities={allEntities} />

      <AnalyticsDashboard finals={finals} />

      <ConversationMemoryPanel
        sessionId={sessionId}
        memory={memory}
        error={memoryError}
        removeCaseMemoryEntry={removeCaseMemoryEntry}
      />

      <SummaryPanel
        sessionId={sessionId}
        summary={memory?.draft_summary ?? null}
        approved={memory?.summary_approved ?? false}
        error={summaryError}
        isGenerating={isGeneratingSummary}
        onGenerate={() => void generateSummary()}
        onApprove={() => void approveSummary()}
      />

      <TimelineView sessionId={sessionId} events={memory?.timeline ?? []} />
    </section>
  );
}
