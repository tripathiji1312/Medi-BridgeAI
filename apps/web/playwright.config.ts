import { defineConfig, devices } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "../..");

// Windows/POSIX venv layout differs; both are gitignored (.venv*/), created
// per README.md's local-dev instructions or by ci-e2e.yml before this runs.
function venvPython(serviceDir: string): string {
  return process.platform === "win32"
    ? path.join(repoRoot, serviceDir, ".venv/Scripts/python.exe")
    : path.join(repoRoot, serviceDir, ".venv/bin/python");
}

const GATEWAY_PORT = 4100;
const SPEECH_PIPELINE_PORT = 8101;
const CLINICAL_NLP_PORT = 8102;
const ORCHESTRATOR_PORT = 8104;
const WEB_PORT = 5273;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false, // shared backend servers -- avoid cross-test interference
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    trace: "retain-on-failure",
    // Feeds the pre-recorded Hindi fixture as the "microphone" instead of a
    // real device, and auto-grants the mic permission prompt -- lets the
    // consultation flow be driven end-to-end without a real audio device.
    launchOptions: {
      args: [
        "--use-fake-device-for-media-stream",
        "--use-fake-ui-for-media-stream",
        `--use-file-for-fake-audio-capture=${path.join(
          repoRoot,
          "services/speech-pipeline/tests/fixtures/sample_utterance.wav",
        )}`,
      ],
    },
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: `"${venvPython("services/speech-pipeline")}" -m uvicorn app.main:app --host 0.0.0.0 --port ${SPEECH_PIPELINE_PORT}`,
      cwd: path.join(repoRoot, "services/speech-pipeline"),
      port: SPEECH_PIPELINE_PORT,
      reuseExistingServer: !process.env.CI,
      env: {
        MEDIBRIDGE_FIXTURE_MODE: "1",
        PYTHONPATH: ".",
        CLINICAL_NLP_URL: `http://localhost:${CLINICAL_NLP_PORT}`,
        ORCHESTRATOR_URL: `http://localhost:${ORCHESTRATOR_PORT}`,
      },
      timeout: 30_000,
    },
    {
      command: `"${venvPython("services/clinical-nlp")}" -m uvicorn app.main:app --host 0.0.0.0 --port ${CLINICAL_NLP_PORT}`,
      cwd: path.join(repoRoot, "services/clinical-nlp"),
      port: CLINICAL_NLP_PORT,
      reuseExistingServer: !process.env.CI,
      env: {
        MEDIBRIDGE_FIXTURE_MODE: "1",
        PYTHONPATH: ".",
      },
      timeout: 30_000,
    },
    {
      command: `"${venvPython("services/orchestrator")}" -m uvicorn app.main:app --host 0.0.0.0 --port ${ORCHESTRATOR_PORT}`,
      cwd: path.join(repoRoot, "services/orchestrator"),
      port: ORCHESTRATOR_PORT,
      reuseExistingServer: !process.env.CI,
      env: {
        PYTHONPATH: ".",
        // Phase 7: orchestrator's POST .../summary/generate calls
        // clinical-nlp's /summarize endpoint directly -- without this it
        // silently defaults to localhost:8002 (this service's normal dev
        // port), which is wrong here since E2E runs clinical-nlp on 8102.
        CLINICAL_NLP_URL: `http://localhost:${CLINICAL_NLP_PORT}`,
      },
      timeout: 30_000,
    },
    {
      command: `npx tsx src/server.ts`,
      cwd: path.join(repoRoot, "services/gateway"),
      port: GATEWAY_PORT,
      reuseExistingServer: !process.env.CI,
      env: {
        GATEWAY_PORT: String(GATEWAY_PORT),
        JWT_SECRET: "e2e-test-secret",
        SPEECH_PIPELINE_WS_URL: `ws://localhost:${SPEECH_PIPELINE_PORT}/ws/transcribe`,
        ORCHESTRATOR_URL: `http://localhost:${ORCHESTRATOR_PORT}`,
      },
      timeout: 30_000,
    },
    {
      command: `npx vite --port ${WEB_PORT} --strictPort`,
      cwd: __dirname,
      port: WEB_PORT,
      reuseExistingServer: !process.env.CI,
      env: {
        VITE_GATEWAY_HTTP_URL: `http://localhost:${GATEWAY_PORT}`,
        VITE_GATEWAY_WS_URL: `ws://localhost:${GATEWAY_PORT}/ws/transcribe`,
      },
      timeout: 30_000,
    },
  ],
});
