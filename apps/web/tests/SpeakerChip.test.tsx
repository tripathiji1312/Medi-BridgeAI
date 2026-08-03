import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SpeakerChip } from "../src/components/shared/SpeakerChip";
import { ThemeProvider } from "../src/theme/ThemeProvider";

describe("SpeakerChip", () => {
  it("shows the confidence percentage and current role, defaulting to Unassigned", () => {
    render(
      <ThemeProvider>
        <SpeakerChip speakerLabel="speaker_a" confidence={0.87} role="unassigned" onAssignRole={vi.fn()} />
      </ThemeProvider>,
    );

    expect(screen.getByText(/Unassigned \(87% confidence\)/)).toBeInTheDocument();
  });

  it("calls onAssignRole with the new role, never silently applying it itself", () => {
    const onAssignRole = vi.fn();
    render(
      <ThemeProvider>
        <SpeakerChip speakerLabel="speaker_a" confidence={0.87} role="unassigned" onAssignRole={onAssignRole} />
      </ThemeProvider>,
    );

    fireEvent.change(screen.getByLabelText("Assign role for speaker_a"), { target: { value: "doctor" } });

    expect(onAssignRole).toHaveBeenCalledWith("doctor");
    // The component itself doesn't re-render as "Doctor" until the parent
    // feeds the new role back in via props -- it never assumes its own
    // suggestion was accepted (human-in-the-loop, Blueprint Section 1).
  });
});
