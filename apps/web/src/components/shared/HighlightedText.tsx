import type { MedicalEntity } from "@medibridge/shared-types";
import { entityCategoryColors } from "@medibridge/design-tokens";
import { useTheme } from "../../theme/ThemeProvider";
import { highlightEntities } from "../../utils/highlightEntities";

export interface HighlightedTextProps {
  text: string;
  entities: MedicalEntity[] | null;
}

const CATEGORY_LABEL: Record<MedicalEntity["category"], string> = {
  symptom: "Symptom",
  disease: "Disease",
  medication: "Medication",
  allergy: "Allergy",
  vital_sign: "Vital sign",
  procedure: "Procedure",
};

/** Inline medical keyword highlighting (Blueprint Section 2.2: "inline
 * highlighting in transcript for medicines, diseases, body parts,
 * procedures -- tooltip with plain-language definition"). Falls back to
 * plain unhighlighted text when `entities` is null/empty rather than
 * hiding the transcript text itself (Section 1 Principle 3: no silent
 * data loss). Uses the native `title` attribute for the tooltip -- no new
 * dependency needed for a plain-text hover label. */
export function HighlightedText({ text, entities }: HighlightedTextProps) {
  const { mode, colors } = useTheme();

  if (!entities || entities.length === 0) {
    return <>{text}</>;
  }

  const segments = highlightEntities(text, entities);

  return (
    <>
      {segments.map((segment, index) => {
        if (!segment.entity) {
          return <span key={index}>{segment.text}</span>;
        }
        const entity = segment.entity;
        const color = entityCategoryColors[mode][entity.category] ?? colors.textPrimary;
        const confidencePct = Math.round(entity.confidence * 100);
        const tooltip = `${CATEGORY_LABEL[entity.category]}: ${entity.canonical_name}${
          entity.canonical_code ? ` (${entity.canonical_code})` : ""
        } -- ${entity.definition} [${confidencePct}% match${entity.is_fuzzy_match ? ", fuzzy" : ""}]`;
        return (
          <mark
            key={index}
            title={tooltip}
            style={{
              background: "transparent",
              color,
              borderBottom: `2px solid ${color}`,
              cursor: "help",
            }}
          >
            {segment.text}
          </mark>
        );
      })}
    </>
  );
}
