import { useLiveTranscript } from "../../hooks/useLiveTranscript";
import { useTheme } from "../../theme/ThemeProvider";

const GATEWAY_WS_URL = "ws://localhost:4000/ws/transcribe";

/** Phase 1 scope: text-only, no UI polish. Raw bilingual/diarized display,
 * waveform, etc. are Phase 3 (Blueprint Section 8). */
export function LiveTranscriptPanel() {
  const { colors } = useTheme();
  const { consentGiven, isActive, events, error, start, stop } = useLiveTranscript({
    gatewayWsUrl: GATEWAY_WS_URL,
  });

  const finals = events.filter((e) => e.type === "final" && e.segment);
  const latestPartial = [...events].reverse().find((e) => e.type === "partial" && e.segment);

  return (
    <section aria-label="Live transcript" style={{ color: colors.textPrimary }}>
      {!consentGiven ? (
        <button onClick={() => void start()}>Start consultation (I consent to audio recording)</button>
      ) : (
        <button onClick={stop}>Stop consultation</button>
      )}

      <p role="status">{isActive ? "Recording" : consentGiven ? "Connecting…" : "Not recording"}</p>

      {error && (
        <p role="alert" style={{ color: colors.danger }}>
          {error}
        </p>
      )}

      <ul aria-live="polite" aria-label="Transcript">
        {finals.map((event) => (
          <li key={event.utterance_id}>{event.segment?.text}</li>
        ))}
        {latestPartial && <li style={{ opacity: 0.6 }}>{latestPartial.segment?.text} …</li>}
      </ul>
    </section>
  );
}
