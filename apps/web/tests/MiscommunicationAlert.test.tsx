import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MiscommunicationAlert } from "../src/components/alerts/MiscommunicationAlert";
import { ThemeProvider } from "../src/theme/ThemeProvider";

describe("MiscommunicationAlert", () => {
  it("renders as an ARIA alert with the reason, never a bare label", () => {
    render(
      <ThemeProvider>
        <MiscommunicationAlert
          result={{
            consistent: false,
            similarity_score: 0.4,
            negation_flip_detected: false,
            reason: "Back-translation diverges from the original (similarity 0.40 < 0.75).",
          }}
        />
      </ThemeProvider>,
    );

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(/diverges from the original/);
  });

  it("calls out a negation mismatch specifically", () => {
    render(
      <ThemeProvider>
        <MiscommunicationAlert
          result={{
            consistent: false,
            similarity_score: 0.9,
            negation_flip_detected: true,
            reason: "Negation mismatch between the original and its back-translation.",
          }}
        />
      </ThemeProvider>,
    );

    expect(screen.getByRole("alert")).toHaveTextContent(/negation mismatch/i);
  });
});
