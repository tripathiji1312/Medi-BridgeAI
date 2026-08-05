import { describe, expect, it } from "vitest";
import { computeSessionAnalytics } from "../src/utils/analytics";
import type { TranscriptEvent } from "@medibridge/shared-types";

function baseEvent(overrides: Partial<TranscriptEvent> = {}): TranscriptEvent {
  return {
    type: "final",
    utterance_id: "u1",
    session_id: "s1",
    segment: { text: "text", is_final: true, confidence: 0.9, start_ms: 0, end_ms: 1000, language: "hi" },
    error: null,
    latency_ms: null,
    translation: null,
    translation_error: null,
    tts: null,
    tts_error: null,
    speaker: null,
    speaker_error: null,
    back_translation: null,
    back_translation_error: null,
    miscommunication: null,
    miscommunication_error: null,
    confidence_v2: null,
    confidence_band: null,
    entities: null,
    entities_error: null,
    translation_entities: null,
    translation_entities_error: null,
    emergency: null,
    emergency_error: null,
    emotion: null,
    emotion_error: null,
    risk: null,
    risk_error: null,
    ...overrides,
  };
}

describe("computeSessionAnalytics", () => {
  it("returns zeroed/null analytics for no events", () => {
    const result = computeSessionAnalytics([]);

    expect(result.consultationDurationMs).toBe(0);
    expect(result.symptomCount).toBe(0);
    expect(result.avgConfidenceV2).toBeNull();
    expect(result.avgAsrConfidence).toBeNull();
    expect(result.speakingRatio).toEqual({});
    expect(result.emotionTrend).toEqual({});
  });

  it("computes consultation duration as the span from earliest start to latest end", () => {
    const events = [
      baseEvent({ segment: { text: "a", is_final: true, confidence: 0.9, start_ms: 0, end_ms: 1000, language: "hi" } }),
      baseEvent({ segment: { text: "b", is_final: true, confidence: 0.9, start_ms: 2000, end_ms: 3500, language: "hi" } }),
    ];

    const result = computeSessionAnalytics(events);

    expect(result.consultationDurationMs).toBe(3500);
  });

  it("computes speaking ratio proportional to each speaker's total duration", () => {
    const events = [
      baseEvent({
        segment: { text: "a", is_final: true, confidence: 0.9, start_ms: 0, end_ms: 1000, language: "hi" },
        speaker: { speaker_label: "speaker_a", confidence: 0.9 },
      }),
      baseEvent({
        segment: { text: "b", is_final: true, confidence: 0.9, start_ms: 1000, end_ms: 4000, language: "hi" },
        speaker: { speaker_label: "speaker_b", confidence: 0.9 },
      }),
    ];

    const result = computeSessionAnalytics(events);

    expect(result.speakingRatio.speaker_a).toBeCloseTo(0.25);
    expect(result.speakingRatio.speaker_b).toBeCloseTo(0.75);
  });

  it("counts distinct symptom entities across hindi and translation sides", () => {
    const events = [
      baseEvent({
        entities: [
          {
            text: "fever", category: "symptom", canonical_name: "fever", canonical_code: "R50.9",
            definition: "d", confidence: 1, start_char: 0, end_char: 5, is_fuzzy_match: false,
          },
        ],
        translation_entities: [
          {
            text: "fever", category: "symptom", canonical_name: "fever", canonical_code: "R50.9",
            definition: "d", confidence: 1, start_char: 0, end_char: 5, is_fuzzy_match: false,
          },
          {
            text: "cough", category: "symptom", canonical_name: "cough", canonical_code: "R05",
            definition: "d", confidence: 1, start_char: 0, end_char: 5, is_fuzzy_match: false,
          },
          {
            text: "paracetamol", category: "medication", canonical_name: "paracetamol", canonical_code: null,
            definition: "d", confidence: 1, start_char: 0, end_char: 5, is_fuzzy_match: false,
          },
        ],
      }),
    ];

    const result = computeSessionAnalytics(events);

    // fever (deduped across both sides) + cough = 2 distinct symptoms; medication excluded.
    expect(result.symptomCount).toBe(2);
  });

  it("averages confidence_v2 only across events where it's present", () => {
    const events = [
      baseEvent({ confidence_v2: 0.8 }),
      baseEvent({ confidence_v2: 0.6 }),
      baseEvent({ confidence_v2: null }),
    ];

    const result = computeSessionAnalytics(events);

    expect(result.avgConfidenceV2).toBeCloseTo(0.7);
  });

  it("averages raw ASR segment confidence", () => {
    const events = [
      baseEvent({ segment: { text: "a", is_final: true, confidence: 0.9, start_ms: 0, end_ms: 100, language: "hi" } }),
      baseEvent({ segment: { text: "b", is_final: true, confidence: 0.7, start_ms: 100, end_ms: 200, language: "hi" } }),
    ];

    const result = computeSessionAnalytics(events);

    expect(result.avgAsrConfidence).toBeCloseTo(0.8);
  });

  it("tallies emotion labels across utterances", () => {
    const events = [
      baseEvent({ emotion: { label: "anxious", confidence: 0.7, reason: "r", disclaimer: "d" } }),
      baseEvent({ emotion: { label: "anxious", confidence: 0.6, reason: "r", disclaimer: "d" } }),
      baseEvent({ emotion: { label: "calm", confidence: 0.5, reason: "r", disclaimer: "d" } }),
    ];

    const result = computeSessionAnalytics(events);

    expect(result.emotionTrend.anxious).toBe(2);
    expect(result.emotionTrend.calm).toBe(1);
  });
});
