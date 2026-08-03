import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { colorTokens, type ColorTokens, type ThemeMode } from "@medibridge/design-tokens";

const STORAGE_KEY = "medibridge-theme-mode";

interface ThemeContextValue {
  mode: ThemeMode;
  toggle: () => void;
  colors: ColorTokens;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

function readStoredMode(): ThemeMode {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === "dark" ? "dark" : "light";
  } catch {
    // localStorage can throw in some environments (private browsing,
    // disabled storage) -- fall back to the default rather than crashing.
    return "light";
  }
}

/** Dark/light mode persists across reload (Blueprint Section 12.4 E2E
 * requirement: "Dark/light mode toggle persists across session and
 * reload"). localStorage failures degrade to the default mode silently
 * here (not user-facing AI output, so the fail-loud rule doesn't apply --
 * worst case the user re-toggles). */
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>(readStoredMode);
  const value = useMemo<ThemeContextValue>(
    () => ({
      mode,
      toggle: () =>
        setMode((m) => {
          const next = m === "light" ? "dark" : "light";
          try {
            window.localStorage.setItem(STORAGE_KEY, next);
          } catch {
            // Non-fatal -- see readStoredMode's comment above.
          }
          return next;
        }),
      colors: colorTokens[mode],
    }),
    [mode],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return ctx;
}
