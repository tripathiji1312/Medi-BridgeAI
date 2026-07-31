import { ThemeProvider, useTheme } from "./theme/ThemeProvider";
import { HealthStatus } from "./components/shared/HealthStatus";

function Shell() {
  const { colors, mode, toggle } = useTheme();

  return (
    <div style={{ background: colors.background, color: colors.textPrimary, minHeight: "100vh" }}>
      <header style={{ padding: 16, borderBottom: `1px solid ${colors.border}` }}>
        <h1 style={{ margin: 0, fontSize: 20 }}>MediBridge AI</h1>
        <button onClick={toggle}>Switch to {mode === "light" ? "dark" : "light"} mode</button>
      </header>

      {/* Blueprint Section 11.4 — persistent, non-dismissible-without-acknowledgment disclaimer. */}
      <div role="alert" style={{ background: colors.warning, color: "#fff", padding: 8 }}>
        MediBridge AI assists communication. It does not diagnose. Always confirm critical
        information verbally.
      </div>

      <main style={{ padding: 16 }}>
        <HealthStatus />
      </main>
    </div>
  );
}

export function App() {
  return (
    <ThemeProvider>
      <Shell />
    </ThemeProvider>
  );
}
