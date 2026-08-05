import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
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

  // Mirrors the active palette onto CSS custom properties so plain global
  // CSS (index.css -- buttons, form controls, card chrome) can react to
  // light/dark mode too, without every one of this app's many panels
  // needing to pass theme colors down as inline styles individually. Purely
  // a presentation-layer hook -- doesn't change any component's markup,
  // text, or ARIA attributes.
  useEffect(() => {
    const root = document.documentElement.style;
    root.setProperty("--color-background", value.colors.background);
    root.setProperty("--color-surface", value.colors.surface);
    root.setProperty("--color-primary", value.colors.primary);
    root.setProperty("--color-primary-contrast", value.colors.primaryContrast);
    root.setProperty("--color-text-primary", value.colors.textPrimary);
    root.setProperty("--color-text-secondary", value.colors.textSecondary);
    root.setProperty("--color-border", value.colors.border);
    root.setProperty("--color-danger", value.colors.danger);
    root.setProperty("--color-warning", value.colors.warning);
    root.setProperty("--color-success", value.colors.success);
  }, [value.colors]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return ctx;
}
