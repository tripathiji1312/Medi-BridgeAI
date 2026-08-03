import { ThemeProvider, useTheme } from "./theme/ThemeProvider";
import { HealthStatus } from "./components/shared/HealthStatus";
import { LiveTranscriptPanel } from "./components/panels/LiveTranscriptPanel";

/** Dashboard shell: panels layout (Blueprint Section 2.4/8 Phase 3) --
 * a status sidebar (model/latency health, consent state) alongside the
 * main live-transcript panel. Grid, not a component library, to stay
 * dependency-light per the "no UI polish" scope carried through Phase 3. */
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

      <main
        style={{
          display: "grid",
          gridTemplateColumns: "240px 1fr",
          gap: 16,
          padding: 16,
        }}
      >
        <aside
          aria-label="Session status"
          style={{
            background: colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: 8,
            padding: 12,
          }}
        >
          <h2 style={{ fontSize: 14, marginTop: 0 }}>System Status</h2>
          <HealthStatus />
        </aside>

        <section
          aria-label="Consultation"
          style={{
            background: colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: 8,
            padding: 16,
          }}
        >
          <LiveTranscriptPanel />
        </section>
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
