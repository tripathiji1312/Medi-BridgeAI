import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { HealthStatus } from "../src/components/shared/HealthStatus";
import { ThemeProvider } from "../src/theme/ThemeProvider";

describe("HealthStatus", () => {
  it("shows a checking state before the gateway responds", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise(() => {})),
    );

    render(
      <ThemeProvider>
        <HealthStatus />
      </ThemeProvider>,
    );

    expect(screen.getByRole("status")).toHaveTextContent("Checking gateway status");
    vi.unstubAllGlobals();
  });

  it("shows a degraded reason string when the gateway is unreachable, never a silent/blank state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new Error("network error"))),
    );

    render(
      <ThemeProvider>
        <HealthStatus />
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveAttribute("data-status", "down");
    });
    expect(screen.getByRole("status")).toHaveTextContent("AI assistance unavailable");
    vi.unstubAllGlobals();
  });

  it("shows an operational status with the service name once healthy", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: "ok", service: "gateway", version: "0.1.0" }),
        } as Response),
      ),
    );

    render(
      <ThemeProvider>
        <HealthStatus />
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveAttribute("data-status", "ok");
    });
    vi.unstubAllGlobals();
  });
});
