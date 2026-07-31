# PROGRESS.md
### Living log — updated every phase. Read this in full before starting any session.

---

## Status Snapshot

- **Current phase:** Phase 1 — Core Speech Pipeline — fully done, including live mic capture
- **Last completed task:** End-to-end live path: browser mic → gateway WS proxy → speech-pipeline ASR → transcript events back to the browser, with a consent gate and visible error/latency state
- **Known issues / deferred items:** see "Deferred" under each session entry below
- **Next recommended task:** Phase 2 — Translation + TTS (MT service HI→EN wired to Phase 1's transcript output, TTS streamed back, confidence scoring v1)

---

## Session Log

### Session 1 — 2026-07-31

**What changed:**
- Created full repo skeleton per Blueprint Section 5 (`apps/web`, `services/{gateway,speech-pipeline,clinical-nlp,vision-service,orchestrator}`, `packages/{shared-types,medical-lexicon,design-tokens}`, `infra/docker`, `infra/k8s`, `.github/workflows`, `scripts/model-eval`, `docs/ADRs`).
- `apps/web`: Vite + React + TypeScript (strict mode) scaffold with a minimal dashboard shell (blue/white theme + dark mode tokens), a `HealthStatus` component that polls the gateway `/health` endpoint, and a Vitest unit test.
- `services/gateway`: Node.js Fastify service with `/health` endpoint, a JWT auth stub (`services/gateway/src/auth`) behind an interface (no real IdP wired yet — explicitly stubbed, documented as a Phase-9 RBAC follow-up), and Vitest tests using `fastify.inject`.
- `services/speech-pipeline`, `services/clinical-nlp`, `services/vision-service`, `services/orchestrator`: Python FastAPI services, each with a `/health` endpoint returning `{status, service, version}`, pydantic strict config, mypy strict config, and pytest tests via `TestClient`. No ML logic yet — placeholders only, per Phase 0 scope (health-check endpoints only).
- `packages/shared-types`: TypeScript types for the cross-service `HealthResponse` contract (first shared contract; more added as pipeline phases land).
- `packages/medical-lexicon`: empty versioned lexicon JSON stub + README describing the intended Hindi/English medical term schema (real lexicon content is Phase 5 scope).
- `packages/design-tokens`: color/spacing/typography tokens for the medical blue/white theme, light + dark mode.
- `infra/docker`: per-service Dockerfiles (multi-stage) + `docker-compose.dev.yml` wiring gateway, all four Python services, Postgres 15, Redis 7, and MinIO for local dev.
- `.github/workflows`: `ci-web.yml`, `ci-services.yml`, `ci-e2e.yml`, `security-scan.yml` — lint + unit test stages wired now; integration/model-eval/chaos stages stubbed with `TODO(Phase N)` markers pointing at the blueprint phase that will fill them in, not silently omitted.
- `docs/COMPLIANCE.md`, `docs/ADRs/0001-record-architecture-decisions.md`: created per blueprint Section 14 and the ADR convention referenced in Section 5.
- `.env.example`, root `README.md`, `LICENSE` created.

**Tests added/passed (all verified green in this environment, not just authored):**
- `apps/web`: 3 Vitest tests (`tests/HealthStatus.test.tsx`) — checking state, degraded/down state with reason string, and ok state — **3 passed**.
- `services/gateway`: 4 Vitest tests — `/health` shape (1) and auth stub: missing token / invalid token / valid token round-trip (3) — **4 passed**.
- `services/speech-pipeline`, `clinical-nlp`, `vision-service`, `orchestrator`: 1 pytest test each asserting `/health` returns 200 with `{status: "ok", service: "<name>", version: "0.1.0"}` — **4 passed** (1 per service).
- `mypy --strict` and `ruff check` run clean (zero errors) on all four Python services' `app/` packages.
- **Total: 11/11 tests green.** Commands used: `npm run test:js` (root) and `pytest -q` / `mypy app` / `ruff check .` per Python service dir.

**Deferred (explicitly, with reason):**
- **Docker Compose stack not smoke-tested** — Docker Desktop/Engine is not installed in this environment (`docker` command not found). Compose file is authored and internally consistent but unverified end-to-end. Action needed: run `docker compose -f infra/docker/docker-compose.dev.yml up` once Docker is available and confirm all health checks pass.
- **CI workflows are unverified against real GitHub Actions** — no GitHub remote exists yet for this repo. Syntax-checked by hand only; the underlying commands (`npm test`, `pytest`, `mypy`, `ruff`) were verified locally in this session and are known to pass.
- **Python version note:** local dev environment runs Python 3.14. `pydantic==2.9.2`/`fastapi==0.115.4` (as originally pinned) have no prebuilt wheel for 3.14 and fail to build from source here (no Rust/MSVC toolchain). Requirements were relaxed to range pins (`pydantic>=2.9.2,<3.0.0`, `fastapi>=0.115.4,<0.142.0`, `uvicorn[standard]>=0.32.0,<0.36.0`) so pip resolves a version with a compatible wheel (resolved to pydantic 2.13.x / fastapi ~0.141.x in this session). Note for CI: pin `python-version: "3.11"` in `.github/workflows/ci-services.yml` (already done) so CI resolves the originally-intended dependency versions; the range pins keep local dev on newer Python working without forcing a CI version bump.
- **Auth is a stub, not real auth** — `services/gateway/src/auth` issues/validates a symmetric-secret JWT for local dev only; OAuth2/OIDC + MFA (blueprint Section 4/9) is explicitly Phase 9 scope, not done now.
- **No real ML/model calls anywhere** — every Python service's business logic is an empty placeholder returning only health status; this is intentional Phase 0 scope, not a shortfall.

**Assumptions made on ambiguous points:**
- Blueprint doesn't specify a package manager for the JS workspace; chose npm workspaces (already available, no extra install) over pnpm/yarn to avoid introducing a new external dependency without flagging it first (per `AGENT_INSTRUCTIONS.md` Section 1).
- Root TS project uses `strict: true` plus `noUncheckedIndexedAccess` or Python `mypy --strict` per Section 6.2 "type safety enforced"; exact flag set documented in each service's config file rather than restated here.

**Git status:** Git was not available at the start of this session (not installed; `winget install Git.Git` initially failed with a network error reaching GitHub release assets — reproduced identically on retry). The user installed Git for Windows separately mid-session; `git init` was run afterward and the Phase 0 tree committed. `node_modules/`, `.venv*/`, and other build artifacts are excluded via `.gitignore` and were confirmed absent from the initial commit (101 files staged, verified no `node_modules`/`.venv` matches in `git status --short`).

**Next recommended task:** Begin Phase 1 (streaming Hindi ASR → raw transcript over WebSocket, tested against pre-recorded audio fixtures before live mic, with latency instrumentation from day one per Blueprint Section 8).

---

### Session 2 — 2026-07-31 (continued)

**What changed — git remote:**
- User installed Git for Windows independently; confirmed working (`git --version` 2.55.0.windows.3).
- `git init` run, Phase 0 tree committed (`03c38e2`), remote `origin` set to
  `https://github.com/yubair69/MediBridgeAI.git`, pushed and tracking `origin/main`
  (branch renamed `master`→`main` on push per GitHub default).

**What changed — Phase 1 (Core Speech Pipeline, text-only):**
- **ASR provider decision:** user chose a local open-source model (faster-whisper /
  CTranslate2 Whisper) over a commercial streaming API, specifically because it needs
  no third-party data retention agreement (Blueprint Section 6.1 hard constraint) and
  needs no API key/account provisioning I can't do on the user's behalf. Confirmed via
  `AskUserQuestion` before implementing, per `AGENT_INSTRUCTIONS.md` Section 6 ("new
  external API/model call handling patient audio" must be surfaced, not guessed).
- Feasibility-checked `faster-whisper` on this machine's Python 3.14/Windows setup in a
  throwaway venv before committing to the choice: installs and imports cleanly, and a
  real end-to-end smoke test (tiny model, downloaded from Hugging Face Hub) ran against
  the fixture without error.
- `services/speech-pipeline/app/asr/`:
  - `provider.py` — `ASRProvider` Protocol (batch transcribe interface), so the model
    is swappable without touching routing/session logic (`AGENT_INSTRUCTIONS.md`
    Section 3.1 abstraction rule).
  - `schemas.py` — `TranscriptSegment`/`TranscriptEvent` pydantic-strict models;
    every event always carries `confidence` and (when applicable) `latency_ms` — no
    AI value ships without its "why" (Rule 1).
  - `faster_whisper_provider.py` — real provider; imports `faster_whisper`/`numpy`
    lazily inside `__init__` so importing the module (and `app.main`) never requires
    the heavy optional dependency to be installed.
  - `fixture_provider.py` — deterministic digest-keyed test double.
  - `provider_factory.py` — lazy singleton factory for the real provider; the
    WebSocket route catches its `RuntimeError` (raised when `faster-whisper` isn't
    installed) and sends a client-visible `type: "error"` event + closes, instead of
    crashing the process (Blueprint Section 6.1: "no single ML service outage can
    crash the session").
  - `session.py` — `StreamingASRSession`: turns incoming PCM16 chunks into
    partial/final `TranscriptEvent`s using a plain RMS-energy VAD gate (not a model-
    based VAD — see Deferred below) to find utterance boundaries; `end_ms` reflects
    buffered *audio-content* duration, not wall-clock processing time (a fast fixture
    replay processes near-instantly, so wall-clock elapsed time would be meaningless).
- `services/speech-pipeline/app/routes/transcribe_ws.py` — `GET /ws/transcribe`
  WebSocket endpoint, router built via a factory so the provider is injectable
  (tests inject a stub; `app/main.py` injects the real lazy provider).
- `services/speech-pipeline/requirements-asr.txt` — new file: `faster-whisper`,
  `numpy` kept separate from `requirements.txt` so ordinary dev/test installs (which
  exercise `FixtureASRProvider`/stub providers only) stay lightweight; real-model
  tests are opt-in, not part of the default `pytest` run.
- `services/speech-pipeline/pyproject.toml` — added mypy override so
  `faster_whisper`/`numpy` missing-import errors don't fail strict mypy when the
  optional ASR extras aren't installed (matches the requirements split above).
- `services/speech-pipeline/tests/fixtures/` — `generate_fixture.py` + generated
  `sample_utterance.wav`: a **synthetic** two-tone-burst fixture (not real speech —
  see Deferred below), engineered so both utterances have >500ms trailing silence and
  finalize on their own without relying on WebSocket-disconnect flush.

**Tests added/passed (all verified green in this environment):**
- `test_fixture_provider.py` — 2 tests (digest match, `KeyError` on unregistered audio).
- `test_session.py` — 3 tests: two utterances finalize from the fixture with
  `is_final`/`confidence`/`latency_ms` populated; distinct utterance IDs with duration
  bounds; silence-only audio produces zero events and zero provider calls (no wasted
  inference on pure silence).
- `test_transcribe_ws.py` — 2 tests: full WebSocket round trip (fixture streamed in
  ~100ms client-style chunks, both `final` events received with expected shape); the
  provider-unavailable path sends a client-visible error event and closes rather than
  hanging or crashing.
- `test_health.py` — 1 test (unchanged from Phase 0).
- **Total: 8/8 tests green** (`pytest -q` in `services/speech-pipeline`), `mypy --strict`
  and `ruff check` both clean (25 source files checked).
- Two real bugs were caught and fixed by these tests before commit: (1) utterance
  `end_ms` was computed from wall-clock elapsed time, which is ~0 for a fast fixture
  replay — fixed to derive from buffered audio-sample count instead; (2) the original
  fixture's trailing silence (0.3s) was shorter than the 500ms finalize threshold, so
  the second utterance never naturally finalized over the WebSocket (only disconnect-
  triggered flushes do, and those aren't delivered to an already-gone client) — fixed
  by lengthening the fixture's trailing silence to 0.8s.

**Deferred (explicitly, with reason):**
- **VAD is a plain RMS-energy gate, not a model-based VAD** (webrtcvad/Silero). Enough
  to segment the fixture deterministically and keep Phase 1 dependency-light; a
  proper model-based VAD is Phase 6 (noise/accent robustness) scope per the blueprint,
  not a Phase 1 blocker.
- **No real spoken-Hindi audio fixture exists yet.** `sample_utterance.wav` is
  synthetic (two sine-wave tone bursts), generated because no vetted-license real
  Hindi audio source and no offline Hindi TTS engine were available in this build
  environment. It validates pipeline plumbing (VAD segmentation, partial/final event
  sequencing, latency instrumentation) but **not** ASR accuracy/WER — that requires a
  real gold-set fixture and belongs in `scripts/model-eval/` per Blueprint Section
  11.3, which is explicitly out of scope until Phase 1's pipeline exists (it now does).
  **Action needed:** source or record real (synthetic-consent or fully synthetic-TTS)
  Hindi medical-consultation audio before any WER/accuracy claim is made.
  Confirmed with the real `faster-whisper` "tiny" model in this session: it correctly
  returned zero segments for the synthetic tone fixture (it isn't speech) — proof the
  real integration path works, not proof of transcription accuracy.
  - **Live microphone input is not wired yet** — Blueprint Section 8 Phase 1 scope is
  explicitly "pre-recorded fixtures before live mic"; `apps/web` audio capture
  (WebRTC/Web Audio API) and the client-side WebSocket connection to
  `/ws/transcribe` are not implemented this session. Next session should wire
  `apps/web/src/hooks/useAudioCapture` (per the Section 5 file tree) before moving to
  Phase 2, or explicitly defer it to land alongside Phase 3's UI work — flag which to
  the user if ambiguous when picked back up.
- **Latency budget (ASR partials <300ms, Blueprint Section 6.1) is instrumented but not
  yet CI-enforced.** `latency_ms` is present on every event (so it's visible/auditable
  now), but there's no automated perf-budget check in `ci-services.yml` yet — that's
  Blueprint Section 13.1 stage 7, reasonably deferred until there's a realistic (non-
  synthetic-tone) audio workload to benchmark against.
- **Concurrent-connection thread-safety of the shared `FasterWhisperASRProvider`
  singleton** (one model instance reused across all WebSocket sessions via
  `lru_cache`) has not been load-tested. Acceptable for Phase 1's single-session
  text-only scope; flag for Phase 10 (Resilience & Chaos / load testing) if not
  revisited sooner.
- **`ci-services.yml` does not install/test the ASR extras** (`requirements-asr.txt`)
  — CI runs against `FixtureASRProvider`/stub providers only, consistent with keeping
  CI fast per the split rationale above. A real-model smoke test (like the one run
  manually this session) could be added as an opt-in/nightly job later.

**Assumptions made on ambiguous points:**
- Interpreted "streaming Hindi ASR" for Phase 1 as: batch-transcribe-per-utterance
  (VAD-segmented) with periodic partial re-transcription of the growing buffer, not
  true token-by-token incremental decoding — faster-whisper doesn't natively support
  the latter, and Blueprint Section 8 Phase 1 only asks for "raw transcript over
  WebSocket" with partial+final semantics, not a specific decoding strategy.
- `PARTIAL_INTERVAL_MS`/`SILENCE_HANG_MS`/`RMS_SPEECH_THRESHOLD` values in
  `session.py` are reasonable placeholders, not tuned against real speech/noise —
  flagged for revisit once real audio is available (see VAD/fixture deferrals above).

**Next recommended task:** Wire `apps/web` live microphone capture to
`/ws/transcribe` (or explicitly defer to Phase 3 — ask the user which), then begin
Phase 2 (HI→EN machine translation service wired to this session's transcript output,
TTS streamed back, confidence scoring v1).

---

### Session 3 — 2026-08-01

**What changed — live microphone path closes out Phase 1's "audio capture" item:**

Resolved the ambiguity flagged at the end of Session 2 (wire live mic now vs. defer to
Phase 3) toward completing it now: Blueprint Section 8 Phase 1 literally lists "Audio
capture" as the first line item and says "test with pre-recorded fixtures **before**
live mic," implying live mic is still Phase 1 scope, just sequenced after fixture
testing — which was already done. Phase 3 is "no UI polish" dashboard work, not basic
capture. Proceeded without re-asking per Auto Mode guidance (reasonable call, not a
new external dependency/data-flow decision).

- **`services/gateway`**: added a `/ws/transcribe` WebSocket **proxy** (`src/ws/transcribeProxy.ts`)
  so client audio routes browser → gateway → speech-pipeline, matching the Blueprint
  Section 3.1 architecture diagram exactly, instead of having the frontend connect
  directly to speech-pipeline (which would have bypassed the gateway's "WS session
  mgmt" ownership per `AGENT_INSTRUCTIONS.md` Section 2 and required rework later).
  Forwards binary audio frames upstream and JSON transcript events back **verbatim**
  — no ML/clinical interpretation in the gateway, per the same boundary rule. On
  upstream connection failure, sends a client-visible `type: "error"` event and closes,
  rather than hanging. New deps: `@fastify/websocket`, `ws` (mechanical implementation
  of the already-approved WebSocket transport in Blueprint Section 4, not a new
  architectural dependency — proceeded without asking).
- **`apps/web`**: 
  - `src/audio/pcm.ts` — pure downsampling/PCM16-encoding helpers (no browser API
    surface, fully unit-testable).
  - `src/hooks/useAudioCapture.ts` — mic capture via `getUserMedia` + `AudioContext`
    + `ScriptProcessorNode` (deprecated API, chosen over `AudioWorkletNode` to avoid
    a separate worklet-module-loading path for Phase 1; flagged as a follow-up
    migration below), with injectable `getUserMedia`/`createAudioContext` factories
    so it's testable without a real browser.
  - `src/services/transcriptSocket.ts` — thin injectable WebSocket wrapper; malformed
    server messages produce a visible error event instead of throwing/being dropped.
  - `src/hooks/useLiveTranscript.ts` — combines the two above; recording only starts
    after an explicit user click (**consent gate**, Blueprint Section 14: informed
    consent before recording starts).
  - `src/components/panels/LiveTranscriptPanel.tsx` — minimal (Phase 1: "text-only, no
    UI polish") consent button, recording/connecting status (`role="status"`), visible
    error banner (`role="alert"`), and an `aria-live="polite"` transcript list —
    accessibility live-region requirement (Blueprint Section 2.5) satisfied from the
    start, not bolted on later. Wired into `App.tsx` below the existing disclaimer.
  - `packages/shared-types`: added `TranscriptSegment`/`TranscriptEvent` interfaces
    mirroring `services/speech-pipeline/app/asr/schemas.py`, used by both the gateway
    proxy's implicit contract and the web client.

**Bugs found and fixed while wiring this up (not part of the original plan):**
- **Pre-existing Phase 0 bug**: `packages/design-tokens` typed `colorTokens` with
  `as const`, which made `colorTokens.light` and `colorTokens.dark` structurally
  incompatible literal types — `ThemeProvider.tsx`'s `colorTokens[mode]` only
  type-checked because **`npm run build` (real `tsc`) had never been run** in Phase 0,
  only `vitest` (which doesn't type-check by default). Caught this session when
  `apps/web`'s build was run for the first time. Fixed by giving `colorTokens` an
  explicit `Record<ThemeMode, ColorTokens>` type instead of relying on literal
  inference. **Action taken:** added `npm run build` to `ci-web.yml` (it only ran
  lint+test before) so this class of bug is caught in CI going forward, and added a
  `typecheck` script + CI step for `services/gateway` for the same reason (it had an
  analogous latent `tsconfig`/`rootDir` mismatch that only `tsc -p` surfaced, not
  `vitest`). **Lesson for future sessions: `vitest`/`pytest` passing is not proof a
  service type-checks or builds — run the actual build/typecheck command too before
  calling a phase done.**
- Two `react-hooks/exhaustive-deps` lint warnings in `useAudioCapture.ts` (fallback
  functions recreated every render, feeding a `useCallback` dependency array) — fixed
  by moving the fallbacks into refs, consistent with the existing `onChunkRef` pattern.

**Tests added/passed (all verified green in this environment):**
- `apps/web`: +14 tests — `pcm.test.ts` (5), `useAudioCapture.test.tsx` (3),
  `transcriptSocket.test.ts` (3), `LiveTranscriptPanel.test.tsx` (3). Total apps/web:
  **17/17 green**, plus `npm run build` (real `tsc -b && vite build`) and `npm run lint`
  both clean.
- `services/gateway`: +3 tests (`transcribeProxy.test.ts`) covering binary forwarding,
  event forwarding, and the upstream-unreachable error path (a real `ws` server used
  as the fake upstream, not a mock, so this is a genuine integration test). Total
  gateway: **7/7 green**, plus `npm run typecheck`/`build`/`lint` all clean.
- **Combined this session: 24/24 JS tests green**; Python suite re-verified unchanged
  and still green (11/11, mypy/ruff clean across all four services).

**Deferred (explicitly, with reason):**
- **`ScriptProcessorNode` is deprecated** in favor of `AudioWorkletNode`. Kept for
  Phase 1 because `AudioWorkletNode` requires loading a separate worklet module file
  (`audioContext.audioWorklet.addModule(url)`), which adds real complexity for a
  "text-only, no UI polish" phase without changing functional behavior. Migrate before
  any production pilot — modern browsers still support `ScriptProcessorNode` but may
  deprecate it further.
- **No end-to-end manual verification of the real browser mic path** (i.e., no human
  clicked the consent button in an actual browser against a running gateway +
  speech-pipeline stack this session) — verified via unit/integration tests with
  injected fakes only, consistent with this being a headless build environment. Next
  session with a real browser available should do one manual smoke test.
- **Audio format assumption**: `useAudioCapture` always downsamples to 16kHz to match
  `FasterWhisperASRProvider`'s `EXPECTED_SAMPLE_RATE`; if a user's mic/AudioContext
  reports a rate below 16kHz, `downsampleBuffer` will throw (by design — "no
  numeric fabrication/silent upsampling," Blueprint Section 11.1) but this hasn't been
  tested against unusual real hardware sample rates.
- Everything already deferred in Session 2 (model-based VAD, real spoken-Hindi
  fixtures, CI latency-budget enforcement, concurrent-session load testing,
  ASR-extras not in CI) still applies unchanged.

**Next recommended task:** Phase 2 — Translation + TTS: wire an HI→EN MT service
(`services/speech-pipeline/app/mt`) onto this session's transcript output, stream TTS
audio back to the other party's client, and add confidence scoring v1 (ASR confidence
only; MT self-consistency is Phase 4).

---

*(Append new session entries above this line as work continues. Do not delete prior entries — this file is the durable cross-session memory substitute.)*
