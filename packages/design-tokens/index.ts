// Design tokens for the "modern medical blue/white" theme (Blueprint Section 2.4).
// Consumed by apps/web/src/theme. Kept framework-agnostic (plain objects) so it can
// back Tailwind config, CSS variables, or React Native later without rework.

export type ThemeMode = "light" | "dark";

export interface ColorTokens {
  background: string;
  surface: string;
  primary: string;
  primaryContrast: string;
  textPrimary: string;
  textSecondary: string;
  border: string;
  success: string;
  warning: string;
  danger: string;
  confidenceGreen: string;
  confidenceYellow: string;
  confidenceRed: string;
}

// Typed as Record<ThemeMode, ColorTokens> (not `as const`) so `light` and
// `dark` share one structural type -- `as const` would infer each variant's
// exact string literals, making colorTokens[mode] fail to type-check
// wherever `mode` isn't statically known (e.g. ThemeProvider's useState).
export const colorTokens: Record<ThemeMode, ColorTokens> = {
  light: {
    background: "#F7FAFC",
    surface: "#FFFFFF",
    primary: "#1565C0",
    primaryContrast: "#FFFFFF",
    textPrimary: "#0F1B2D",
    textSecondary: "#4A5A70",
    border: "#D8E1EA",
    success: "#1E8E3E",
    warning: "#B58500",
    danger: "#C62828",
    // Confidence bands — Blueprint Section 2.2
    confidenceGreen: "#1E8E3E",
    confidenceYellow: "#B58500",
    confidenceRed: "#C62828",
  },
  dark: {
    background: "#0B1420",
    surface: "#12202F",
    primary: "#5B9BEA",
    primaryContrast: "#0B1420",
    textPrimary: "#EAF1F8",
    textSecondary: "#9FB0C3",
    border: "#22384D",
    success: "#4CBB6F",
    warning: "#E0B23A",
    danger: "#E5645A",
    confidenceGreen: "#4CBB6F",
    confidenceYellow: "#E0B23A",
    confidenceRed: "#E5645A",
  },
};

export const spacingTokens = {
  xs: "4px",
  sm: "8px",
  md: "16px",
  lg: "24px",
  xl: "32px",
} as const;

export const typographyTokens = {
  fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif",
  sizeBody: "14px",
  sizeHeading: "20px",
  sizeCaption: "12px",
} as const;

export const confidenceBand = (score: number): "green" | "yellow" | "red" => {
  if (score >= 85) return "green";
  if (score >= 60) return "yellow";
  return "red";
};
