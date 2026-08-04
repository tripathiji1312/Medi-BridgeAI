import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { HighlightedText } from "../src/components/shared/HighlightedText";
import { ThemeProvider } from "../src/theme/ThemeProvider";
import type { MedicalEntity } from "@medibridge/shared-types";

const feverEntity: MedicalEntity = {
  text: "fever",
  category: "symptom",
  canonical_name: "fever",
  canonical_code: "R50.9",
  definition: "An elevated body temperature, often a sign of infection or illness.",
  confidence: 1.0,
  start_char: 9,
  end_char: 14,
  is_fuzzy_match: false,
};

describe("HighlightedText", () => {
  it("renders plain text unchanged when there are no entities", () => {
    render(
      <ThemeProvider>
        <HighlightedText text="I have a fever" entities={null} />
      </ThemeProvider>,
    );
    expect(screen.getByText("I have a fever")).toBeInTheDocument();
  });

  it("wraps a matched entity in a <mark> with a tooltip carrying the definition, never a bare label", () => {
    render(
      <ThemeProvider>
        <HighlightedText text="I have a fever" entities={[feverEntity]} />
      </ThemeProvider>,
    );
    const mark = screen.getByText("fever");
    expect(mark.tagName).toBe("MARK");
    expect(mark.getAttribute("title")).toMatch(/elevated body temperature/);
    expect(mark.getAttribute("title")).toMatch(/R50\.9/);
    expect(mark.getAttribute("title")).toMatch(/100% match/);
  });

  it("notes fuzzy matches in the tooltip", () => {
    const fuzzy = { ...feverEntity, confidence: 0.85, is_fuzzy_match: true };
    render(
      <ThemeProvider>
        <HighlightedText text="I have a fever" entities={[fuzzy]} />
      </ThemeProvider>,
    );
    expect(screen.getByText("fever").getAttribute("title")).toMatch(/fuzzy/);
  });
});
