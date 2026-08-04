import type { MedicalEntity } from "@medibridge/shared-types";

export interface TextSegment {
  text: string;
  entity: MedicalEntity | null;
}

/**
 * Splits `text` into a sequence of plain/highlighted segments based on
 * each entity's start_char/end_char (Blueprint Section 2.2: inline
 * keyword highlighting). Entities are assumed non-overlapping and sorted
 * left-to-right, which is what clinical-nlp's extractor guarantees --
 * but this function re-sorts and skips any entity whose span doesn't
 * actually match `text` at that position, rather than trusting the input
 * blindly (defense in depth: a client should never render a highlight
 * that doesn't correspond to real text, per Blueprint Section 11.1's
 * grounding rule).
 */
export function highlightEntities(text: string, entities: MedicalEntity[]): TextSegment[] {
  const valid = entities
    .filter((e) => e.start_char >= 0 && e.end_char <= text.length && e.start_char < e.end_char)
    .filter((e) => text.slice(e.start_char, e.end_char) === e.text)
    .sort((a, b) => a.start_char - b.start_char);

  const segments: TextSegment[] = [];
  let cursor = 0;

  for (const entity of valid) {
    if (entity.start_char < cursor) {
      continue; // overlapping with an already-placed entity -- skip rather than corrupt ordering
    }
    if (entity.start_char > cursor) {
      segments.push({ text: text.slice(cursor, entity.start_char), entity: null });
    }
    segments.push({ text: text.slice(entity.start_char, entity.end_char), entity });
    cursor = entity.end_char;
  }
  if (cursor < text.length) {
    segments.push({ text: text.slice(cursor), entity: null });
  }

  return segments;
}
