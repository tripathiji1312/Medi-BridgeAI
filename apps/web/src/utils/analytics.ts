import type { EmotionCategory, TranscriptEvent } from "@medibridge/shared-types";

export interface SessionAnalytics {
  /** Total audio duration spanned by all finalized utterances (earliest
   * start_ms to latest end_ms) -- audio-domain duration, not wall-clock
   * session length, since that's the real signal available client-side
   * without inventing a separate session-start timestamp. */
  consultationDurationMs: number;
  /** speaker_label -> fraction of total spoken duration (0-1). Empty if no
   * utterance carries a speaker assignment. */
  speakingRatio: Record<string, number>;
  /** Count of distinct canonical symptom names mentioned (Hindi original
   * or English translation side, deduped). */
  symptomCount: number;
  /** Mean of confidence_v2 across utterances where it was computed (Section
   * 2.2's "Translation Confidence Score ... rolling session average").
   * Null if no utterance has a confidence_v2 yet. */
  avgConfidenceV2: number | null;
  /** Mean of the raw per-utterance ASR confidence -- this build's honest
   * stand-in for the blueprint's "accuracy stats" metric (Section 2.4):
   * there's no ground-truth transcript to compute real accuracy against,
   * so ASR's own self-reported confidence is the closest real signal
   * available, not a fabricated number. */
  avgAsrConfidence: number | null;
  /** Count of each emotion label observed across utterances that had one. */
  emotionTrend: Partial<Record<EmotionCategory, number>>;
}

function mean(values: number[]): number | null {
  if (values.length === 0) return null;
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

export function computeSessionAnalytics(finals: TranscriptEvent[]): SessionAnalytics {
  const withSegment = finals.filter((e) => e.segment !== null);

  const starts = withSegment.map((e) => e.segment!.start_ms);
  const ends = withSegment.map((e) => e.segment!.end_ms);
  const consultationDurationMs = starts.length > 0 ? Math.max(...ends) - Math.min(...starts) : 0;

  const speakingDurations: Record<string, number> = {};
  for (const event of withSegment) {
    if (!event.speaker) continue;
    const duration = event.segment!.end_ms - event.segment!.start_ms;
    speakingDurations[event.speaker.speaker_label] = (speakingDurations[event.speaker.speaker_label] ?? 0) + duration;
  }
  const totalSpeakingDuration = Object.values(speakingDurations).reduce((sum, d) => sum + d, 0);
  const speakingRatio: Record<string, number> =
    totalSpeakingDuration > 0
      ? Object.fromEntries(
          Object.entries(speakingDurations).map(([label, duration]) => [label, duration / totalSpeakingDuration]),
        )
      : {};

  const symptomNames = new Set<string>();
  for (const event of finals) {
    for (const entity of [...(event.entities ?? []), ...(event.translation_entities ?? [])]) {
      if (entity.category === "symptom") symptomNames.add(entity.canonical_name);
    }
  }

  const confidenceV2Values = finals.filter((e) => e.confidence_v2 !== null).map((e) => e.confidence_v2!);
  const asrConfidenceValues = withSegment.map((e) => e.segment!.confidence);

  const emotionTrend: Partial<Record<EmotionCategory, number>> = {};
  for (const event of finals) {
    if (!event.emotion) continue;
    emotionTrend[event.emotion.label] = (emotionTrend[event.emotion.label] ?? 0) + 1;
  }

  return {
    consultationDurationMs,
    speakingRatio,
    symptomCount: symptomNames.size,
    avgConfidenceV2: mean(confidenceV2Values),
    avgAsrConfidence: mean(asrConfidenceValues),
    emotionTrend,
  };
}
