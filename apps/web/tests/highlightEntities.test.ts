import { describe, expect, it } from "vitest";
import { highlightEntities } from "../src/utils/highlightEntities";
import type { MedicalEntity } from "@medibridge/shared-types";

function entity(overrides: Partial<MedicalEntity>): MedicalEntity {
  return {
    text: "fever",
    category: "symptom",
    canonical_name: "fever",
    canonical_code: "R50.9",
    definition: "An elevated body temperature.",
    confidence: 1.0,
    start_char: 0,
    end_char: 5,
    is_fuzzy_match: false,
    ...overrides,
  };
}

describe("highlightEntities", () => {
  it("returns the whole text as one plain segment when there are no entities", () => {
    expect(highlightEntities("I have a fever", [])).toEqual([{ text: "I have a fever", entity: null }]);
  });

  it("splits text into plain/highlighted segments around a single entity", () => {
    const e = entity({ text: "fever", start_char: 9, end_char: 14 });
    const segments = highlightEntities("I have a fever", [e]);
    expect(segments).toEqual([
      { text: "I have a ", entity: null },
      { text: "fever", entity: e },
    ]);
  });

  it("handles an entity in the middle with plain text on both sides", () => {
    const e = entity({ text: "fever", start_char: 9, end_char: 14 });
    const segments = highlightEntities("I have a fever today", [e]);
    expect(segments).toEqual([
      { text: "I have a ", entity: null },
      { text: "fever", entity: e },
      { text: " today", entity: null },
    ]);
  });

  it("sorts out-of-order entities by start_char before segmenting", () => {
    // "fever and cough" -- cough is at index 10-15.
    const second = entity({ text: "cough", category: "symptom", start_char: 10, end_char: 15 });
    const first = entity({ text: "fever", start_char: 0, end_char: 5 });
    const segments = highlightEntities("fever and cough", [second, first]);
    expect(segments.map((s) => s.text)).toEqual(["fever", " and ", "cough"]);
  });

  it("drops an entity whose span text doesn't match the claimed text (grounding check)", () => {
    // start_char/end_char point at "have " but `text` claims "fever" -- a
    // corrupted/malicious payload should never render as a highlight.
    const bad = entity({ text: "fever", start_char: 2, end_char: 7 });
    const segments = highlightEntities("I have a fever", [bad]);
    expect(segments).toEqual([{ text: "I have a fever", entity: null }]);
  });

  it("drops an entity with an out-of-range span", () => {
    const bad = entity({ text: "fever", start_char: 100, end_char: 105 });
    const segments = highlightEntities("short text", [bad]);
    expect(segments).toEqual([{ text: "short text", entity: null }]);
  });

  it("skips overlapping entities rather than corrupting segment order", () => {
    const a = entity({ text: "high fever", category: "symptom", start_char: 0, end_char: 10 });
    const b = entity({ text: "fever", category: "symptom", start_char: 5, end_char: 10 });
    const segments = highlightEntities("high fever today", [a, b]);
    // `a` is placed first (lower start_char); `b` overlaps it and is skipped.
    expect(segments).toEqual([
      { text: "high fever", entity: a },
      { text: " today", entity: null },
    ]);
  });
});
