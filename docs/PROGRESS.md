# PROGRESS.md
### Living log — updated every phase. Read this in full before starting any session.

---

## Status Snapshot

- **Current phase:** Phase 0 — Foundations (in progress)
- **Last completed task:** Repo skeleton + service scaffolds with health checks (this session)
- **Known issues / deferred items:** see "Deferred" under the session entry below
- **Next recommended task:** Finish Phase 0 (CI wiring verification, Docker Compose smoke test once Docker is available), then start Phase 1 (Core Speech Pipeline, text-only)

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

*(Append new session entries above this line as work continues. Do not delete prior entries — this file is the durable cross-session memory substitute.)*
