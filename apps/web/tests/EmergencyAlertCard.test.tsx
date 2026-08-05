import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { EmergencyAlertCard } from "../src/components/alerts/EmergencyAlertCard";
import { ThemeProvider } from "../src/theme/ThemeProvider";

describe("EmergencyAlertCard", () => {
  it("renders as an alertdialog with the reason, never a bare label", () => {
    render(
      <ThemeProvider>
        <EmergencyAlertCard
          utteranceId="u1"
          reason="Detected emergency keyword(s): chest pain."
          onDismiss={vi.fn().mockResolvedValue(true)}
          playAlertSound={vi.fn()}
        />
      </ThemeProvider>,
    );

    expect(screen.getByRole("alertdialog", { name: "Emergency alert" })).toBeInTheDocument();
    expect(screen.getByText(/Detected emergency keyword\(s\): chest pain\./)).toBeInTheDocument();
  });

  it("plays the alert sound exactly once on mount, not on every re-render", () => {
    const playAlertSound = vi.fn();
    const { rerender } = render(
      <ThemeProvider>
        <EmergencyAlertCard
          utteranceId="u1"
          reason="Detected emergency keyword(s): chest pain."
          onDismiss={vi.fn().mockResolvedValue(true)}
          playAlertSound={playAlertSound}
        />
      </ThemeProvider>,
    );

    rerender(
      <ThemeProvider>
        <EmergencyAlertCard
          utteranceId="u1"
          reason="Detected emergency keyword(s): chest pain."
          onDismiss={vi.fn().mockResolvedValue(true)}
          playAlertSound={playAlertSound}
        />
      </ThemeProvider>,
    );

    expect(playAlertSound).toHaveBeenCalledTimes(1);
  });

  it("requires a reason before dismissing -- a bare click does not call onDismiss", () => {
    const onDismiss = vi.fn().mockResolvedValue(true);
    render(
      <ThemeProvider>
        <EmergencyAlertCard
          utteranceId="u1"
          reason="Detected emergency keyword(s): chest pain."
          onDismiss={onDismiss}
          playAlertSound={vi.fn()}
        />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: /dismiss alert/i }));

    expect(screen.getByRole("alert")).toHaveTextContent(/reason is required/i);
    expect(onDismiss).not.toHaveBeenCalled();
  });

  it("calls onDismiss with the typed reason once submitted", async () => {
    const onDismiss = vi.fn().mockResolvedValue(true);
    render(
      <ThemeProvider>
        <EmergencyAlertCard
          utteranceId="u1"
          reason="Detected emergency keyword(s): chest pain."
          onDismiss={onDismiss}
          playAlertSound={vi.fn()}
        />
      </ThemeProvider>,
    );

    fireEvent.change(screen.getByLabelText(/reason for dismissing/i), {
      target: { value: "Patient clarified: no chest pain, mistranslation" },
    });
    fireEvent.click(screen.getByRole("button", { name: /dismiss alert/i }));

    await waitFor(() => {
      expect(onDismiss).toHaveBeenCalledWith("Patient clarified: no chest pain, mistranslation");
    });
  });
});
