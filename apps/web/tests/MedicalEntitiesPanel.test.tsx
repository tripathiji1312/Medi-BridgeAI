import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MedicalEntitiesPanel } from "../src/components/panels/MedicalEntitiesPanel";
import { ThemeProvider } from "../src/theme/ThemeProvider";
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

describe("MedicalEntitiesPanel", () => {
  it("shows a placeholder rather than an empty section when no entities have been detected", () => {
    render(
      <ThemeProvider>
        <MedicalEntitiesPanel entities={[]} />
      </ThemeProvider>,
    );
    expect(screen.getByText(/No medical terms detected yet/)).toBeInTheDocument();
  });

  it("groups entities under their category headings", () => {
    render(
      <ThemeProvider>
        <MedicalEntitiesPanel
          entities={[
            entity({ category: "symptom", canonical_name: "fever" }),
            entity({ category: "medication", canonical_name: "paracetamol", canonical_code: null }),
          ]}
        />
      </ThemeProvider>,
    );
    expect(screen.getByText("Symptoms")).toBeInTheDocument();
    expect(screen.getByText("Medications")).toBeInTheDocument();
    expect(screen.getByText(/fever/)).toBeInTheDocument();
    expect(screen.getByText(/paracetamol/)).toBeInTheDocument();
  });

  it("dedupes repeated mentions of the same canonical term within a category", () => {
    render(
      <ThemeProvider>
        <MedicalEntitiesPanel
          entities={[
            entity({ category: "symptom", canonical_name: "fever" }),
            entity({ category: "symptom", canonical_name: "fever", text: "high fever" }),
          ]}
        />
      </ThemeProvider>,
    );
    expect(screen.getAllByText(/fever/)).toHaveLength(1);
  });

  it("only renders category headings that have at least one entity", () => {
    render(
      <ThemeProvider>
        <MedicalEntitiesPanel entities={[entity({ category: "allergy", canonical_name: "penicillin allergy" })]} />
      </ThemeProvider>,
    );
    expect(screen.getByText("Allergies")).toBeInTheDocument();
    expect(screen.queryByText("Symptoms")).not.toBeInTheDocument();
  });
});
