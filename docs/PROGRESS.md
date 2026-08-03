# PROGRESS.md
### Living log — updated every phase. Read this in full before starting any session.

---

## Status Snapshot

- **Current phase:** Phase 3 — Bilingual Transcript UI + Speaker Diarization — fully
  done, including the Playwright E2E gate from Blueprint Section 10's Definition of
  Done (see Session 4)
- **Last completed task:** Pre-Phase-4 verification audit (found/fixed 4 real infra
  bugs — CI's `python-services` job missing `pytest-cov`, the Docker image never
  installing the real ASR/MT/diarization models, the gateway's Docker Compose entry
  having no route to speech-pipeline, stray ungitignored `.coverage` files) followed
  by closing the E2E gap it surfaced: a real Playwright suite (9 specs) now drives an
  actual browser against real (not mocked) gateway + speech-pipeline processes
  running in a new deterministic `MEDIBRIDGE_FIXTURE_MODE`, all green.
- **Known issues / deferred items:** see "Deferred" under each session entry below.
- **Next recommended task:** Phase 4 — Conversation Memory + Miscommunication Detector
  (rolling context + structured case memory, back-translation consistency check,
  confidence score v2)

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

### Session 4 — 2026-08-01

**What changed — Phase 2 (Translation + TTS):**

- **MT engine decision:** asked before implementing (same category as the Phase 1 ASR
  decision — new model/provider touching transcript data, `AGENT_INSTRUCTIONS.md`
  Section 6). User chose local NLLB-200-distilled-600M over IndicTrans2 (extra unvetted
  tooling) and Claude-API-based MT (third-party retention). Feasibility-checked
  `torch`/`transformers`/`sentencepiece` install on this Python 3.14/Windows setup
  first (succeeded) before committing to the choice.
- **TTS engine**: `facebook/mms-tts-eng` via the same `transformers`/`torch` stack
  already required for NLLB — **not** separately confirmed with the user, since it's
  the same category of decision (local self-hosted model, no third-party retention)
  already resolved for MT this phase; noted here as an assumption per
  `AGENT_INSTRUCTIONS.md` Section 1 rather than re-asking.
- `services/speech-pipeline/app/mt/`: `provider.py` (Protocol), `schemas.py`
  (`TranslationSegment` — deliberately **no** MT-specific confidence field yet, since
  Blueprint Section 8 Phase 2 scope is explicitly "confidence scoring v1: ASR
  confidence only, MT self-consistency added next" — inventing one now would violate
  the "no numeric fabrication" rule, Section 11.1), `nllb_provider.py` (real, lazy
  import), `fixture_provider.py` (deterministic test double), `provider_factory.py`.
- `services/speech-pipeline/app/tts/`: same shape — `provider.py`, `schemas.py`
  (`TTSAudioSegment`: base64 PCM16 + sample_rate, sent **inline in the JSON event**
  rather than as a separate binary WS frame, trading ~33% bandwidth overhead for a
  much simpler client protocol; flagged as a latency optimization to revisit later,
  not a Phase 2 blocker), `mms_provider.py`, `fixture_provider.py`, `provider_factory.py`.
- `services/speech-pipeline/requirements-mt.txt`: `transformers`, `torch`,
  `sentencepiece` — kept out of the base dev install (heavy, optional), same pattern
  as `requirements-asr.txt`. `pyproject.toml` mypy overrides extended for these too.
- `app/asr/schemas.py`: `TranscriptEvent` extended with `translation`,
  `translation_error`, `tts`, `tts_error` — all four independent of each other and of
  the existing `error` field, so an MT or TTS outage never drops the underlying Hindi
  transcript (Blueprint Section 7.2 degraded-mode rule). This does mean `app/asr`
  now imports from `app/mt`/`app/tts` for these types — a minor layering wrinkle
  (documented inline) but still within the single `speech-pipeline` service, not a
  cross-service boundary violation.
- `app/routes/transcribe_ws.py`: `create_transcribe_router` gained optional
  `get_mt_provider`/`get_tts_provider` params (default `None` — Phase 1 tests that
  don't pass them are unaffected). New `_enrich_final_event` helper: **only runs on
  final events, never partials** (translating unstable text wastes compute and would
  flicker on screen); catches any MT/TTS exception and attaches it as `*_error`
  instead of letting it propagate and kill the connection.
- `packages/shared-types`: added `TranslationSegment`/`TTSAudioSegment`, extended
  `TranscriptEvent` to match.
- `apps/web`: `src/audio/wav.ts` — wraps the raw PCM16 TTS audio in a minimal WAV
  header (raw PCM has no container and can't play directly from a data URL).
  `LiveTranscriptPanel.tsx` now shows the English translation text next to each
  finalized Hindi segment and an `<audio controls>` element for the synthesized
  speech — **no autoplay**, so playback is a deliberate clinician/patient action
  (Blueprint Section 1: human-in-the-loop always), and degraded-mode warnings
  (`role="alert"`) render instead of a silent gap when translation or TTS fails.

**Tests added/passed (all verified green in this environment):**
- `services/speech-pipeline`: +7 tests — `test_mt_fixture_provider.py` (2),
  `test_tts_fixture_provider.py` (2), plus 3 new `test_transcribe_ws.py` cases:
  successful MT+TTS enrichment (and confirms MT is called exactly once per **final**,
  never per partial), MT-failure degrades gracefully (raw transcript still delivered,
  TTS correctly never runs without a translation to speak), TTS-failure degrades
  gracefully (transcript + translation still delivered). Total: **15/15 green**,
  `mypy --strict` and `ruff` both clean (37 source files).
- `apps/web`: +6 tests — `wav.test.ts` (1, validates the WAV header byte-for-byte),
  plus 2 new `LiveTranscriptPanel.test.tsx` cases (renders translation text + a
  `data:audio/wav;base64,...` playable element on success; shows a visible degraded-
  mode warning, not a silent gap, on translation failure). Total: **20/20 green**,
  plus `npm run build`/`lint` both clean.
- Gateway required **no changes** for this phase — its proxy already forwards JSON
  events verbatim (Phase 1 design), so the new `translation`/`tts` fields pass through
  automatically; re-ran its 7/7 tests to confirm no regression.
- **Combined this session: 42/42 tests green** (15 Python + 27 JS).

**Deferred (explicitly, with reason):**
- **Real-model NLLB smoke test: completed, with a finding worth recording.** The
  unauthenticated HuggingFace Hub download (~2.4GB) was slow (rate-limited, not a code
  problem) but finished later in the same session. The *first* smoke-test run used
  romanized Hindi ("mujhe bukhaar hai", Latin script) as a quick typing shortcut — the
  real model **echoed it back unchanged instead of translating**. Investigated rather
  than shrugged off: traced it to `transformers` 5.14.1 removing `forced_bos_token_id`
  from `transformers/generation/*` entirely (confirmed via grep — zero matches in the
  installed package) yet the tokenizer's `src_lang`/`forced_bos_token_id` mechanism
  still works via a different internal path (verified: the generated sequence's second
  token was correctly `eng_Latn`, id 256047) — so forcing the target-language tag
  works fine. The echo was NOT a code bug: NLLB-200 was trained on Hindi in
  **Devanagari script**; feeding it romanized/Latin-script "Hindi" is out-of-
  distribution, and the model degenerately copied the input instead of translating
  gibberish-to-it. Re-ran with real Devanagari input ("मुझे बुखार है") and got a
  correct, fluent translation: **"I have a fever."** This matters operationally: it's
  fine, because faster-whisper's real Hindi ASR output is Devanagari script by
  default, matching what MT will actually receive in production — but it's a reminder
  that ad-hoc smoke-test inputs must match the real upstream data shape, not just be
  "close enough for a quick check." `nllb_provider.py` required **no code changes**.
- **`mms-tts-eng` real-model smoke test: completed.** `MmsTTSProvider.synthesize("I have
  a fever.", "en")` produced 58,028 bytes of valid PCM16 audio at 16kHz — the full
  MT→TTS chain has now been verified end-to-end with real models, not just fixtures.
- **No MT-specific confidence score.** Per Blueprint Section 8 Phase 2 scope
  ("confidence scoring v1: ASR confidence only"), `TranslationSegment` carries no
  confidence field. MT self-consistency scoring (back-translation-based) is Phase 4.
- **TTS audio sent inline as base64 JSON**, not raw binary WS frames — simpler
  protocol, ~33% bandwidth cost. Revisit as a latency optimization once real TTS
  latency is measured against the <800ms first-byte target (Blueprint Section 2.1);
  not measured this session (no completed real-model run yet).
- **No conversation-memory conditioning for MT** (Blueprint Section 3.2 step 5
  mentions conditioning translation on rolling context for disambiguation) — that's
  explicitly Phase 4 scope ("Conversation Memory + Miscommunication Detector"), not
  Phase 2.
- **No back-translation consistency check** — also explicitly Phase 4 scope per the
  blueprint phase description itself.
- Everything already deferred in Sessions 2-3 (model-based VAD, real spoken-Hindi
  fixtures, CI latency-budget enforcement, concurrent-session load testing, ASR/MT
  extras not in CI, no manual real-browser smoke test) still applies unchanged.

**Next recommended task:** Complete the deferred NLLB/mms-tts real-model smoke test,
then begin Phase 3 (Bilingual Transcript UI + Speaker Diarization) — dashboard shell
with the blue/white theme, live bilingual transcript with timestamps, diarization
integrated into the ASR pipeline, waveform animation.

---

### Session 3 — 2026-08-01 — Phase 3: Bilingual Transcript UI + Speaker Diarization

**Diarization approach decision:** user explicitly wants real ML used where reasonable
("we need ml"), so the earlier `AskUserQuestion` menu (manual toggle / real ML via
pyannote.audio / two-mic channels) was resolved in favor of real ML, but **not**
`pyannote.audio`: its diarization pipeline is gated on HuggingFace (license acceptance +
token I can't provision on the user's behalf). Chose **SpeechBrain's ECAPA-TDNN**
(`speechbrain/spkrec-ecapa-voxceleb`) instead — an ungated, local/self-hosted speaker-
embedding model — paired with a lightweight **online 2-speaker clustering** algorithm
written for this project (not a pretrained diarization pipeline): nearest-centroid
assignment with a novelty threshold to decide when a second voice is genuinely new,
capped at 2 speakers (Doctor/Patient) since this is a 2-party consultation, and
deliberately **not retroactive** (an utterance's label is never rewritten later, per
Blueprint Section 1 Principle 4 "AI never overwrites the human-readable transcript").

**What changed — backend (`services/speech-pipeline`):**
- `app/diarization/`: `schemas.py` (`SpeakerAssignment` — content-neutral
  `speaker_label` + confidence; diarization can tell voices apart but not which is the
  doctor), `provider.py` (`SpeakerEmbeddingProvider` Protocol), `fixture_provider.py`
  (digest-keyed test double), `ecapa_provider.py` (real provider), `diarizer.py`
  (`SpeakerDiarizer` — the online clustering logic, pure Python/math, zero ML
  dependencies itself so it's fully unit-testable without any model), `provider_factory.py`
  (lazy singleton for the *embedding model*, which is stateless and shareable — the
  *diarizer* itself is instantiated fresh per WebSocket connection since its clustering
  state must never leak across sessions/patients).
- `app/asr/session.py`: added a bounded (`max 8`) `utterance_id -> audio bytes` cache,
  populated whenever an utterance finalizes, with a `get_utterance_audio()` accessor.
  Needed because a single `push_chunk()` call can finalize more than one utterance (a
  large chunk containing two full utterances back-to-back — exactly what the Phase 1
  fixture does), so "the last emitted utterance's audio" would have been wrong; keying
  by utterance_id instead makes the lookup correct regardless of batching.
- `app/asr/schemas.py`: `TranscriptEvent` gained `speaker`/`speaker_error` (final-only,
  independently degradable from translation/tts — same pattern as Phase 2).
- `app/routes/transcribe_ws.py`: refactored `_enrich_final_event` into three independent
  stages (`_run_translation` → `_run_tts` → `_run_diarization`), each catching its own
  failures so one stage's outage never blocks stages that already succeeded. The
  diarizer is constructed once per connection at accept-time (not lazily per-utterance)
  so a broken embedding model degrades the whole session once, with a clear reason,
  rather than silently retrying on every utterance.
- `requirements-diarization.txt`: speechbrain + torch, kept separate from
  `requirements.txt` (same rationale as `requirements-asr.txt`/`requirements-mt.txt` —
  heavy optional deps, ordinary test runs use `FixtureEmbeddingProvider`).
- **Windows-specific fix, worth remembering**: SpeechBrain's `EncoderClassifier.from_hparams`
  defaults to `LocalStrategy.SYMLINK` for its model cache, which raised
  `OSError: WinError 1314` (symlink privilege) on this machine. Fixed by passing
  `local_strategy=LocalStrategy.COPY_SKIP_CACHE` explicitly in `ecapa_provider.py`.

**What changed — frontend (`apps/web`):**
- `src/audio/pcm.ts`: added `computeRmsLevel` (pure, unit-tested) for a live level meter.
- `src/hooks/useAudioCapture.ts`: added an optional `onLevel` callback fired alongside
  `onChunk`, so a waveform/level UI doesn't need its own separate audio tap.
- `src/hooks/useLiveTranscript.ts`: exposes `level` (0 whenever not actively recording).
- `src/hooks/useSpeakerRoles.ts`: client-side-only `speaker_label -> Doctor/Patient/
  Unassigned` map. Not persisted to the server yet — that's orchestrator/session-state
  territory (Phase 4+); explicitly a human-in-the-loop UI action, never inferred.
- `src/components/shared/WaveformMeter.tsx`: a bar-meter (not a literal scrolling
  canvas waveform) driven by `level` — conveys "audio is flowing and how loud" without
  a canvas renderer, matching the "no UI polish" scope carried through this phase.
- `src/components/shared/SpeakerChip.tsx`: color-coded chip (new `speakerA`/`speakerB`
  design tokens, distinct from the semantic success/warning/danger colors) + confidence
  + a role `<select>` that calls back to the parent rather than assuming its own
  suggestion was accepted.
- `src/utils/time.ts`: `formatMsAsTimestamp` for per-utterance timestamps.
- `App.tsx`: dashboard shell — a status sidebar (health) + main consultation panel,
  panels-layout grid per Blueprint Section 2.4/8 Phase 3 (not a component library, kept
  dependency-light).
- `LiveTranscriptPanel.tsx`: now shows timestamps, the waveform meter, and the speaker
  chip/role-assignment control per finalized utterance.
- `packages/design-tokens`: added `speakerA`/`speakerB` color tokens (light + dark).
- `packages/shared-types`: added `SpeakerAssignment`, extended `TranscriptEvent`.

**Tests added/passed (all verified green in this environment):**
- `test_diarizer.py` — 5 tests: first utterance seeds speaker_a; a clearly different
  voice becomes speaker_b; a similar voice groups with the existing speaker rather than
  spawning a new one; a third voice folds into its nearest existing cluster rather than
  spawning a speaker_c; labeling is not retroactive (an earlier call keeps its label
  even after a later near-duplicate updates the centroid).
- `test_diarization_fixture_provider.py` — 2 tests.
- `test_transcribe_ws.py` — 3 new tests: successful diarization attaches a speaker
  assignment to every final; an embedding-extraction failure mid-session still delivers
  the transcript (degraded, not dropped); the embedding model being unavailable at
  connection time degrades the whole session with a clear `speaker_error`.
- Backend total: **25/25 tests green**, `mypy --strict` and `ruff` clean (45 source files).
- `pcm.test.ts` (+4: `computeRmsLevel`), `useAudioCapture.test.tsx` (+1: `onLevel`),
  `time.test.ts` (+3), `WaveformMeter.test.tsx` (+2), `SpeakerChip.test.tsx` (+2),
  `useSpeakerRoles.test.ts` (+3), `LiveTranscriptPanel.test.tsx` (+1: speaker chip +
  timestamps + role assignment interaction).
- Frontend total: **43/43 tests green** (apps/web 36 + gateway 7), `tsc -b`/`vite build`
  and `eslint` both clean on apps/web; gateway `tsc` typecheck and build both clean.

**Real-model verification (not just fixtures):**
- Confirmed `speechbrain/spkrec-ecapa-voxceleb` loads and extracts a real 192-dimension
  embedding (after fixing the Windows symlink issue above).
- Ran the full `SpeakerDiarizer` against the real ECAPA provider on the Phase 1 fixture
  audio (split into its two tone-burst halves): the two distinct synthetic voices were
  correctly assigned `speaker_a`/`speaker_b`, and re-running the first half again
  correctly re-matched `speaker_a` — the real clustering pipeline works end-to-end, not
  just the fixture-backed unit tests.

**Deferred (explicitly, with reason):**
- **`NEW_SPEAKER_DISTANCE_THRESHOLD` (0.35 cosine distance) is a qualitative starting
  point, not tuned against a labeled gold set.** The fixture audio (synthetic tone
  bursts at very different frequencies) validates the clustering *logic* but says
  nothing about the right threshold for real human voices, which may be closer together
  in embedding space (same-gender speakers, similar mic distance, etc.). Action needed:
  revisit once real multi-speaker consultation audio is available — same caveat already
  standing for the VAD thresholds since Phase 1.
- **Speaker role assignment (`useSpeakerRoles`) is client-side-only state**, lost on
  page reload and not shared with any other client viewing the same session. Acceptable
  for Phase 3's single-client scope; real persistence is orchestrator/session-state
  territory, Phase 4+ (`services/orchestrator/app/session`, `app/memory`).
- **Concurrent-session load behavior of the shared `EcapaEmbeddingProvider` singleton**
  (one model instance reused across all WebSocket sessions, same pattern as the ASR/MT/
  TTS singletons) has not been load-tested — same standing deferral as Phase 1/2,
  flagged again here since diarization adds a third shared-model contention point.
- **The waveform is a bar-meter, not a literal scrolling waveform.** Matches the
  "waveform animation" *spirit* (Blueprint Section 2.4) without a canvas renderer, kept
  deliberately simple for this phase; revisit if the blueprint's Phase 9/UX-polish pass
  wants a literal waveform.
- **`pretrained_models/` directory**: SpeechBrain's real-provider smoke test downloaded
  model weights to a `pretrained_models/` dir at the repo root (its hardcoded default
  `savedir`). Added to `.gitignore` and deleted from the working tree before commit —
  not source, should never be committed. If a future session sees this directory
  reappear locally, that's expected (regenerated on first real-provider use), not a bug.

**Assumptions made on ambiguous points:**
- Speaker labels are content-neutral (`speaker_a`/`speaker_b`) rather than the model
  guessing "doctor" vs "patient" — diarization has no signal for that, and guessing
  would violate Section 1 Principle 4. Role assignment is an explicit clinician UI
  action. Flagged as the correct interpretation, not a placeholder to fix later.
- Diarization runs after MT/TTS in the enrichment pipeline (translation → speech →
  speaker), not before. Order doesn't affect correctness (each stage is independent and
  keyed off the same finalized segment/translation), but was chosen so a
  diarization-specific slowdown never delays translation/TTS delivery to the client.

**Next recommended task:** Phase 4 — Conversation Memory + Miscommunication Detector:
rolling context window + structured case memory injected into MT/NER prompts, back-
translation (EN→HI) consistency check feeding a composite confidence score v2, and the
first cut of `services/orchestrator/app/memory`.

---

### Session 4 — 2026-08-01 — Full verification pass before Phase 4

User asked for a thorough correctness audit before continuing, specifically to catch
anything that would "waste our efforts." Did a fresh (not cached-trust) pass: clean
`node_modules` reinstall, fresh Python venv, full builds/lints/typechecks/tests for
every service, a manual line-by-line review of the trickiest recent logic (diarizer
clustering, the utterance-audio cache keying, the 3-stage enrichment pipeline), a
field-by-field cross-check of every TS shared-type against its Python pydantic
counterpart, and a read-through of every CI workflow and Docker file against what the
code actually does/needs. Found and fixed four real issues -- none affected the
actual application logic (68/68 tests were genuinely passing before and after), all
were in the "ships correctly but the surrounding infra lies about it" category:

1. **`ci-services.yml`'s `python-services` job has likely been failing on every push
   since Phase 0.** It runs `pytest --cov=app --cov-report=term-missing`, but
   `pytest-cov` was never added to any of the four services' `requirements-dev.txt` --
   reproduced locally (`unrecognized arguments: --cov=app`, exit 4). Fixed by adding
   `pytest-cov==6.0.0` to all four `requirements-dev.txt` files and re-verifying the
   exact CI command passes on all four. This one is a genuine "wasted effort" near-miss:
   every CI run against this repo (4 pushes so far) was almost certainly red on this
   job without anyone (human or agent) noticing, since GitHub Actions were never
   manually checked in-session (no `gh` CLI available, no browser access).
2. **The Docker image for `speech-pipeline` only ever installed `requirements.txt`**
   (fixture providers only) -- `faster-whisper`/`transformers`/`torch`/`speechbrain`
   were never in the image, so every real transcription/translation/TTS/diarization
   request through `docker compose up` would fail with "model not installed," even
   though the service would build and pass its health check cleanly. This would have
   looked like a working deployment right up until someone actually spoke into it.
   Fixed: added `services/speech-pipeline/requirements-full.txt` (unions
   `requirements-asr.txt` + `requirements-mt.txt` + `requirements-diarization.txt`),
   made `Dockerfile.python-service` accept a `REQUIREMENTS_FILE` build arg (default
   `requirements.txt`, unchanged for the other 3 services), and set
   `REQUIREMENTS_FILE: requirements-full.txt` for speech-pipeline specifically in
   `docker-compose.dev.yml`.
3. **`docker-compose.dev.yml`'s `gateway` service had no `SPEECH_PIPELINE_WS_URL`
   set**, so it would fall back to its code default `ws://localhost:8001/...` --
   inside a container, "localhost" resolves to the gateway container itself, not the
   speech-pipeline container, so the WS proxy would never reach it. Fixed by setting
   `SPEECH_PIPELINE_WS_URL: ws://speech-pipeline:8001/ws/transcribe` (Compose service
   name as hostname) and adding `speech-pipeline` to gateway's `depends_on`. Still not
   smoke-tested end-to-end (Docker remains unavailable in this build environment,
   confirmed again this session) -- verified by reading, not running.
4. **`.coverage` files were untracked/ungitignored** -- running the CI-equivalent
   `pytest --cov` command locally (to verify fix #1) left `.coverage` files in 4
   service directories that `git status` would have picked up on next commit. Added
   `.coverage`/`htmlcov/` to `.gitignore`.

Also fixed, lower-stakes: `README.md`'s "Status" line still said "Phase 0" (stale
since the very first commit) and its setup instructions didn't mention
`requirements-full.txt` for anyone wanting the real models instead of fixtures.
`ci-services.yml`'s gateway job ran lint/typecheck/test but not `build` (apps/web's
CI job does); added it for consistency since `tsconfig.build.json` already exists and
the command already verified clean locally.

**What was checked and found already correct** (worth recording so it isn't
re-litigated next session): TS/Python schema field-for-field parity across
`HealthResponse`, `TranscriptSegment`, `TranslationSegment`, `TTSAudioSegment`,
`SpeakerAssignment`, and `TranscriptEvent`; the utterance-audio cache is correctly
keyed by `utterance_id` (not "last emitted"), so the multi-final-per-batch case (which
the Phase 1 fixture literally exercises) resolves correctly; the 3-stage enrichment
pipeline (translation → tts → diarization) correctly runs each stage independently
and only after `push_chunk()` has already populated the audio cache, so there's no
ordering hazard; every `os.environ.get(...)` / `process.env....` read matches its
`.env.example` entry name exactly across both gateway and speech-pipeline;
`pip-audit` and the diarizer's real-model output were re-spot-checked and still hold.

**Deferred, flagged rather than silently skipped:** Blueprint Section 10's Definition
of Done table requires "at least one Playwright scenario exercises the feature
end-to-end through the UI" for user-facing features, and `ci-e2e.yml` has said "Phase 3
introduces apps/web/e2e Playwright specs" since Phase 0 -- but no Playwright specs
exist yet despite Phase 3 shipping substantial UI (consent gate, live transcript,
speaker chips, waveform meter). This is a real, not-yet-closed gap against the
blueprint's own DoD gate, surfaced to the user rather than either silently skipped or
silently implemented (a real browser-driven E2E suite with mocked mic input is a
non-trivial chunk of new work, not a quick fix like the four issues above) -- awaiting
a decision on whether to build it now or continue deferring it with this note intact.

---

### Session 4 (continued) — Closing the Playwright E2E gap

User chose to close the E2E gap flagged above rather than continue deferring it.
Result: a real Playwright suite (9 specs, all green) drives an actual Chromium
browser against **real, running** gateway + speech-pipeline processes — not mocked
WebSocket/fetch like the Vitest component tests use — satisfying Blueprint Section
10's "at least one Playwright scenario exercises the feature end-to-end through the
UI" for every Phase 0-3 user-facing feature that exists so far.

**Key design decision — `MEDIBRIDGE_FIXTURE_MODE`:** running the real ASR/MT/TTS/
diarization models for every E2E run would mean multi-GB downloads and (per this
session's own earlier findings) potentially very slow CPU inference on every CI run
-- impractical for a test suite meant to run nightly and on demand. Added a new
`MEDIBRIDGE_FIXTURE_MODE=1` environment variable that every one of speech-pipeline's
four provider factories (`asr`, `mt`, `tts`, `diarization`) checks *before* falling
back to their real-model branch; when set, each returns a new `Static*Provider`
(`StaticASRProvider`, `StaticMTProvider`, `StaticTTSProvider`,
`StaticEmbeddingProvider`) that returns the same canned, valid response regardless of
input. This is deliberately distinct from the existing digest/text-keyed
`Fixture*Provider` classes (which raise `KeyError` on anything unregistered and exist
for tests that assert on specific inputs) -- the `Static*` providers exist purely so
the **real** `app/main.py` FastAPI server can boot and answer **any** request
deterministically, which is what letting Playwright drive a real browser against a
real server actually requires. Verified the switch itself works both ways: fixture
mode selects every `Static*Provider` (asserted via `isinstance`), and fixture mode
*off* still attempts the real provider (asserted via the same `RuntimeError` the
ASR/MT/TTS/diarization "not installed" path already raises in this dependency-light
test environment).

**Other fixes required along the way (found by actually trying to build this, not
anticipated in advance):**
- **Dark/light mode didn't persist across reload at all** — `ThemeProvider` was
  plain `useState`, no storage. Blueprint Section 12.4 explicitly lists "Dark/light
  mode toggle persists across session and reload" as an E2E scenario, so this was a
  real, shippable gap the E2E work surfaced, not just a testability blocker. Fixed
  with a `localStorage`-backed initializer + write-on-toggle, wrapped in try/catch
  (private browsing / disabled storage degrades to the default rather than crashing
  — not user-facing AI output, so the fail-loud rule doesn't apply here).
- **The gateway URL was hardcoded to `localhost:4000` in two components with no
  override mechanism at all.** E2E needs an isolated port (4100) so it can't collide
  with a real dev server. Rather than a test-only hack, added a proper
  `apps/web/src/config.ts` reading `VITE_GATEWAY_HTTP_URL`/`VITE_GATEWAY_WS_URL` Vite
  env vars (defaulting to the original hardcoded values), which is also just a
  better architecture for real deployment — the app could previously *never* point
  at a non-default gateway at all. Added `vite-env.d.ts` to type the new env vars.
- **Vitest silently started trying to run the new Playwright specs as its own
  tests** — both use `.spec.ts`/`describe`/`test` naming, and vitest's default
  include glob doesn't distinguish them from its own tests. Caught immediately by
  re-running `npm run test:js` after adding the E2E suite (3 files failed with
  "Playwright Test did not expect test.describe() to be called here"). Fixed by
  explicitly excluding `**/e2e/**` in `vite.config.ts`'s `test.exclude` (had to
  restate vitest's other default excludes too, since setting this option replaces
  rather than merges with them — worth remembering for next time this file is
  touched).

**What was verified, concretely:**
- `apps/web/e2e/dashboard.spec.ts` (3 specs): dashboard loads with disclaimer/health
  status/consent button visible; gateway health genuinely reports "operational" via a
  real HTTP round trip; dark/light toggle survives a full `page.reload()`.
- `apps/web/e2e/consultation.spec.ts` (3 specs): recording doesn't start pre-consent;
  clicking consent drives mic capture (via Chromium's
  `--use-fake-device-for-media-stream` + `--use-file-for-fake-audio-capture` feeding
  the existing Phase 1 fixture WAV) through a real WebSocket to a real
  speech-pipeline process and back, rendering the fixture Hindi text, its English
  translation, and a speaker-confidence chip; stopping returns cleanly to the
  consent-gated state.
- `apps/web/e2e/accessibility.spec.ts` (3 specs): the disclaimer is a real ARIA
  `alert`, not just styled text; the consent button is reachable and operable via
  Tab+Enter alone (bounded loop, not a real accessibility-tree scan); the transcript
  list carries `aria-live="polite"`.
- `playwright.config.ts` orchestrates three real `webServer` entries (speech-pipeline
  via `uvicorn` from a venv at the README-documented `services/speech-pipeline/.venv`
  path, gateway via `tsx`, web via `vite`) on non-default ports so a running local
  dev stack never collides with the E2E run.
- `.github/workflows/ci-e2e.yml` rewritten from the Phase-0 placeholder to actually
  set up Python/Node, install Chromium, create the speech-pipeline venv, and run the
  suite — nightly + on-demand (not a required PR check, matching Blueprint Section
  13.2's list of required checks, which doesn't include E2E).
- Full regression pass after all of the above: 34 speech-pipeline + 39 web (Vitest,
  now correctly excluding e2e/) + 7 gateway tests, all green; 9/9 Playwright specs
  green; mypy/ruff/tsc/eslint all clean.

**Deferred, explicitly:**
- The E2E suite covers Phase 0-3 UI only (no login/summary/export flows exist yet to
  test — Blueprint Section 12.4's full "login → ... → export PDF" scenario isn't
  buildable until those phases land). Extend `apps/web/e2e/` incrementally as each
  future phase ships UI, per the Definition of Done, rather than backfilling later.
- The accessibility spec is a targeted manual check (ARIA roles, keyboard reachability),
  not an automated accessibility-tree audit (e.g. `@axe-core/playwright`). Flagged as
  a reasonable follow-up, not added here to avoid scope creep beyond closing the
  specific gap that was raised.
- `ci-e2e.yml` is unverified against real GitHub Actions (same standing caveat as
  every other workflow in this repo — no way to trigger/observe an Actions run from
  this environment). Verified by running the exact same `npm run e2e` command
  locally instead, with real server orchestration.

---

*(Append new session entries above this line as work continues. Do not delete prior entries — this file is the durable cross-session memory substitute.)*
