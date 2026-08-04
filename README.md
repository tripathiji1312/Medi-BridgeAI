# MediBridge AI

Real-time Hindi↔English medical speech-to-speech translation platform — a clinical
**communication aid**, not a diagnostic device.

Start here:
- [`docs/BLUEPRINT.md`](docs/BLUEPRINT.md) — full architecture, scope, and delivery plan.
- [`AGENT_INSTRUCTIONS.md`](AGENT_INSTRUCTIONS.md) — operational rules for the coding agent.
- [`docs/PROGRESS.md`](docs/PROGRESS.md) — living build log, current phase, deferred items.
- [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md) — data handling, retention, consent.

## Status

Phase 4 (Conversation Memory + Miscommunication Detector) complete — see
`docs/PROGRESS.md` for the current session log and what's next.

## Repo layout

See `docs/BLUEPRINT.md` Section 5 for the full annotated tree. Top level:

```
apps/web            React + TypeScript frontend
services/gateway    Node.js Fastify API gateway (auth, routing, WS session mgmt)
services/speech-pipeline   Python FastAPI: ASR, MT, TTS, diarization, noise suppression, emotion
services/clinical-nlp      Python FastAPI: NER, symptoms, risk scoring, emergency detection, summarization
services/vision-service    Python FastAPI: pose/motion/collapse detection
services/orchestrator      Session state, conversation memory, audit log, event fan-out
packages/            Shared types, medical lexicon, design tokens
infra/               Docker Compose (dev), Kubernetes overlays
```

## Local development

Prerequisites: Node.js 20+, Python 3.11+, Docker (for Postgres/Redis/MinIO via
`infra/docker/docker-compose.dev.yml`).

```powershell
# Frontend
cd apps/web; npm install; npm test

# Gateway
cd services/gateway; npm install; npm test

# Each Python service (repeat per service dir)
cd services/speech-pipeline; python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt; pytest

# speech-pipeline only, to run the *real* ASR/MT/TTS/diarization models
# instead of the fixture providers the tests use (heavy: pulls in torch):
pip install -r requirements-full.txt

# E2E (Playwright) -- needs a .venv (requirements-dev.txt is enough --
# MEDIBRIDGE_FIXTURE_MODE means the real model extras aren't needed) in
# each of speech-pipeline, clinical-nlp, and orchestrator first
cd apps/web; npx playwright install --with-deps chromium; npm run e2e
```

## Non-negotiable principles

1. Patient safety over feature completeness.
2. Explainability over black-box confidence — every AI output shows *why*.
3. Fail loud, not silent.
4. Human-in-the-loop always.
5. This is not a diagnostic or emergency-response system.

Full detail: `docs/BLUEPRINT.md` Section 1.
