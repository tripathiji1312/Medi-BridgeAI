import { useLiveTranscript } from "../../hooks/useLiveTranscript";
import { useTheme } from "../../theme/ThemeProvider";
import { pcm16ToWavDataUrl } from "../../audio/wav";

const GATEWAY_WS_URL = "ws://localhost:4000/ws/transcribe";

/** Phase 1-2 scope: text-only/minimal, no UI polish. Full bilingual
 * dashboard layout, diarization, waveforms, etc. are Phase 3 (Blueprint
 * Section 8). Playback uses <audio controls> (no autoplay) so the
 * clinician/patient decides when to hear it -- consistent with
 * "human-in-the-loop always" (Blueprint Section 1). */
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
          <li key={event.utterance_id}>
            <div>{event.segment?.text}</div>

            {event.translation && <div style={{ color: colors.textSecondary }}>{event.translation.text}</div>}
            {event.translation_error && (
              <div role="alert" style={{ color: colors.warning }}>
                Translation unavailable: {event.translation_error}
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
    </section>
  );
}
