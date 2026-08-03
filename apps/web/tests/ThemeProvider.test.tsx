import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { ThemeProvider, useTheme } from "../src/theme/ThemeProvider";

function ToggleButton() {
  const { mode, toggle } = useTheme();
  return <button onClick={toggle}>Current: {mode}</button>;
}

describe("ThemeProvider persistence", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("defaults to light mode when nothing is stored", () => {
    render(
      <ThemeProvider>
        <ToggleButton />
      </ThemeProvider>,
    );
    expect(screen.getByRole("button")).toHaveTextContent("Current: light");
  });

  it("persists the toggled mode to localStorage", () => {
    render(
      <ThemeProvider>
        <ToggleButton />
      </ThemeProvider>,
    );

    act(() => fireEvent.click(screen.getByRole("button")));

    expect(screen.getByRole("button")).toHaveTextContent("Current: dark");
    expect(window.localStorage.getItem("medibridge-theme-mode")).toBe("dark");
  });

  it("reads the persisted mode back on the next mount, simulating a reload", () => {
    window.localStorage.setItem("medibridge-theme-mode", "dark");

    render(
      <ThemeProvider>
        <ToggleButton />
      </ThemeProvider>,
    );

    expect(screen.getByRole("button")).toHaveTextContent("Current: dark");
  });
});
