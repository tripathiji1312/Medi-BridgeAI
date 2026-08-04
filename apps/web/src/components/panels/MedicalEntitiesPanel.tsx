import type { EntityCategory, MedicalEntity } from "@medibridge/shared-types";
import { entityCategoryColors } from "@medibridge/design-tokens";
import { useTheme } from "../../theme/ThemeProvider";

export interface MedicalEntitiesPanelProps {
  entities: MedicalEntity[];
}

const CATEGORY_ORDER: EntityCategory[] = [
  "symptom",
  "disease",
  "medication",
  "allergy",
  "vital_sign",
  "procedure",
];

const CATEGORY_LABEL: Record<EntityCategory, string> = {
  symptom: "Symptoms",
  disease: "Diseases",
  medication: "Medications",
  allergy: "Allergies",
  vital_sign: "Vital signs",
  procedure: "Procedures",
};

/** Categorized medical entities panel (Blueprint Section 2.2: "Medical
 * Entity Recognition: categorization into Symptoms/Diseases/Medications/
 * Allergies/Vital Signs/Procedures"). Dedupes by canonical_name within a
 * category so the same term mentioned twice doesn't repeat -- the panel is
 * a running summary of the conversation, not a per-utterance log (that's
 * what the transcript itself, with inline highlighting, is for). */
export function MedicalEntitiesPanel({ entities }: MedicalEntitiesPanelProps) {
  const { mode, colors } = useTheme();

  if (entities.length === 0) {
    return (
      <section aria-label="Medical entities" style={{ color: colors.textSecondary, fontSize: 12 }}>
        No medical terms detected yet.
      </section>
    );
  }

  const byCategory = new Map<EntityCategory, MedicalEntity[]>();
  for (const entity of entities) {
    const seen = byCategory.get(entity.category) ?? [];
    if (!seen.some((e) => e.canonical_name === entity.canonical_name)) {
      seen.push(entity);
    }
    byCategory.set(entity.category, seen);
  }

  return (
    <section aria-label="Medical entities" style={{ color: colors.textPrimary }}>
      <h3 style={{ fontSize: 14, margin: "0 0 8px" }}>Detected medical terms</h3>
      {CATEGORY_ORDER.filter((category) => byCategory.has(category)).map((category) => (
        <div key={category} style={{ marginBottom: 10 }}>
          <h4
            style={{
              fontSize: 12,
              margin: "0 0 4px",
              color: entityCategoryColors[mode][category],
            }}
          >
            {CATEGORY_LABEL[category]}
          </h4>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12 }}>
            {byCategory.get(category)!.map((entity) => (
              <li key={entity.canonical_name} title={entity.definition}>
                {entity.canonical_name}
                {entity.canonical_code ? ` (${entity.canonical_code})` : ""}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}
