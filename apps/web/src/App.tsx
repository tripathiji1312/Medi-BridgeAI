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
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "14px 24px",
          background: colors.surface,
          borderBottom: `1px solid ${colors.border}`,
          boxShadow: "0 1px 3px rgba(15, 27, 45, 0.06)",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span aria-hidden="true" style={{ fontSize: 22, lineHeight: 1 }}>
            🩺
          </span>
          <div>
            <h1 style={{ margin: 0, fontSize: 18 }}>MediBridge AI</h1>
            <p style={{ margin: 0, fontSize: 11, color: colors.textSecondary }}>
              Real-time Hindi ↔ English medical consultation assistant
            </p>
          </div>
        </div>
        <button onClick={toggle}>Switch to {mode === "light" ? "dark" : "light"} mode</button>
      </header>

      {/* Blueprint Section 11.4 — persistent, non-dismissible-without-acknowledgment disclaimer. */}
      <div
        role="alert"
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          background: colors.warning,
          color: "#fff",
          padding: "8px 24px",
          fontSize: 13,
        }}
      >
        <span aria-hidden="true">⚠️</span>
        MediBridge AI assists communication. It does not diagnose. Always confirm critical
        information verbally.
      </div>

      <main
        style={{
          display: "grid",
          gridTemplateColumns: "260px 1fr",
          gap: 20,
          padding: 24,
          maxWidth: 1280,
          margin: "0 auto",
          alignItems: "start",
        }}
      >
        <aside
          aria-label="Session status"
          style={{
            background: colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: 12,
            padding: 16,
            boxShadow: "0 1px 2px rgba(15, 27, 45, 0.04)",
            position: "sticky",
            top: 88,
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
            borderRadius: 12,
            padding: 20,
            boxShadow: "0 1px 2px rgba(15, 27, 45, 0.04)",
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
