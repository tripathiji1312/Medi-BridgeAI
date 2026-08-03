import { useLiveTranscript } from "../../hooks/useLiveTranscript";
import { useSpeakerRoles } from "../../hooks/useSpeakerRoles";
import { useTheme } from "../../theme/ThemeProvider";
import { pcm16ToWavDataUrl } from "../../audio/wav";
import { formatMsAsTimestamp } from "../../utils/time";
import { WaveformMeter } from "../shared/WaveformMeter";
import { SpeakerChip } from "../shared/SpeakerChip";

const GATEWAY_WS_URL = "ws://localhost:4000/ws/transcribe";

/** Phase 1-3 scope. Playback uses <audio controls> (no autoplay) so the
 * clinician/patient decides when to hear it -- consistent with
 * "human-in-the-loop always" (Blueprint Section 1). */
export function LiveTranscriptPanel() {
  const { colors } = useTheme();
  const { consentGiven, isActive, events, error, level, start, stop } = useLiveTranscript({
    gatewayWsUrl: GATEWAY_WS_URL,
  });
  const { roleFor, assignRole } = useSpeakerRoles();

  const finals = events.filter((e) => e.type === "final" && e.segment);
  const latestPartial = [...events].reverse().find((e) => e.type === "partial" && e.segment);

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

      <ul aria-live="polite" aria-label="Transcript">
        {finals.map((event) => (
          <li key={event.utterance_id} style={{ marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
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
            </div>

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
