# MediBridge AI — Full Engineering Blueprint
### Real-Time Hindi↔English Medical Speech-to-Speech Translation Platform
**Target build environment:** Claude Sonnet 5 via Claude Code in VS Code
**Document purpose:** Single source of truth for architecture, scope, delivery, and quality gates.

---

## 0. How to Use This Blueprint With Claude Code

This document is written to be pasted into a VS Code project as `BLUEPRINT.md` and referenced by Claude Code across sessions, since Claude Code has no persistent memory between sessions beyond files on disk. Recommended setup:

1. Create the repo skeleton (Section 4) first, commit it empty.
2. Drop this file in as `/docs/BLUEPRINT.md` and a trimmed operational checklist as `/docs/AGENT_INSTRUCTIONS.md` (Section 9 is the source for that file).
3. Ask Claude Code to work **one module at a time** (Section 8 phases), each ending in a commit + passing tests, never "build the whole app in one shot."
4. Keep `/docs/PROGRESS.md` updated after every phase — this is the durable memory substitute across sessions.
5. Treat every AI/ML claim (diagnosis-adjacent, symptom, risk level) as **assistive only**, never autonomous — this is a hard product constraint, not just a legal one (see Section 11).

---

## 1. Product Framing & Non-Negotiable Principles

MediBridge AI is a **clinical communication aid**, not a diagnostic device. Every design decision should be evaluated against these principles, in priority order:

1. **Patient safety over feature completeness.** A missing feature is acceptable; a silently wrong translation of "no chest pain" → "chest pain" is not.
2. **Explainability over black-box confidence.** Every AI output (confidence score, risk level, emotion, symptom) must show *why*, not just *what*.
3. **Fail loud, not silent.** If any AI module (ASR, MT, TTS, NER) fails or degrades, the UI must say so — never fall back silently to stale or fabricated data.
4. **Human-in-the-loop always.** The doctor/patient can always see raw transcripts alongside AI output and correct it. AI never overwrites the human-readable transcript.
5. **This is not a diagnostic or emergency-response system.** It assists communication; it does not replace clinical judgment or emergency services. This must be stated in the UI, not just docs.

---

## 2. Complete Feature List

### 2.1 Core Pipeline (from brief, refined)
- Continuous microphone capture with voice-activity detection (VAD), not push-to-talk.
- Streaming Hindi ASR (partial + final transcripts).
- Hindi→English machine translation, sentence-boundary aware, streaming-capable.
- English TTS with natural prosody, low first-byte latency (<800ms target).
- Bilingual live transcript panel with per-utterance timestamps, speaker tag, and edit/correct affordance.
- Speaker diarization (Patient vs Doctor), color-coded, confidence-scored.

### 2.2 Intelligence Layer (from brief, refined + expanded)
- **Conversation Memory**: rolling context window + structured "case memory" (symptoms, meds, allergies mentioned so far) injected into MT/NER prompts for disambiguation. Persisted per session only, cleared/archived at session end per retention policy.
- **Miscommunication Detector**: back-translation consistency check (EN→HI compare to original HI) + semantic-similarity scoring + medical-term specific rule checks (e.g., negation flips: "not diabetic" vs "diabetic").
- **Translation Confidence Score**: composite of ASR confidence, MT model logprob/self-consistency, and back-translation agreement. Displayed 0–100%, color-coded (Green ≥85, Yellow 60–84, Red <60).
- **Emotion Detection**: speech-derived (prosody/pitch/tempo) classifier, 7-class (Calm, Anxious, Fearful, Stressed, Angry, Happy, Neutral) + confidence, shown per utterance, with an explicit "estimated from voice tone, not verified" disclaimer.
- **Symptom Extraction**: NER + curated Hindi/English medical symptom lexicon (ICD-10/SNOMED-mapped where feasible), normalized to canonical symptom codes.
- **Medical Keyword Highlighting**: inline highlighting in transcript for medicines, diseases, body parts, procedures — tooltip with plain-language definition.
- **Medical Entity Recognition**: categorization into Symptoms / Diseases / Medications / Allergies / Vital Signs / Procedures, each with source-span linking back to the transcript (auditability).
- **Risk Level Detection**: Low/Medium/High classifier using symptom set + emergency keyword match + emotion signal, always shown with the *rule or model reason* that triggered it — never a bare label.
- **Emergency Alert System**: keyword/phrase trigger list (breathing difficulty, chest pain radiating, unconsciousness, severe bleeding, stroke signs — FAST criteria) → persistent, dismiss-with-reason banner + audible alert. False-negative-averse design: prefer over-triggering to under-triggering, with easy dismissal logged for audit.
- **AI Meeting Summary**: structured SOAP-like summary (Subjective, Objective-if-available, Assessment-mentioned, Plan) mapped to the brief's fields (Patient Info, Complaints, Symptoms, Diagnoses Mentioned, Medications, Recommendations, Action Items, Follow-up).
- **Timeline Generator**: chronological event stream (symptom mentioned, medication mentioned, alert triggered, risk level changed) with timestamps, exportable.
- **Noise Suppression**: RNNoise-class or model-based suppression pre-ASR; visual "noise level" meter so users know when to intervene.
- **Accent Adaptation**: accent-aware ASR decoding profiles (configurable region hint) + continuous WER self-monitoring with fallback prompt "please repeat" when confidence collapses.

### 2.3 Computer Vision Module
- Webcam-based motion/pose monitoring (opt-in, explicit consent screen, camera indicator always visible).
- Collapse detection: sudden vertical pose drop + stillness heuristic (pose-estimation based, not raw pixel diff, to reduce false positives from lighting).
- Frame-exit detection: patient leaves camera view unexpectedly during active consultation.
- Motionlessness-duration detection with configurable threshold, distinguishing "resting" vs "abnormal stillness" using breathing micro-motion where feasible.
- Emergency notification banner + optional configurable auto-alert integration hook (e.g., notify nursing station) — **disabled by default**, must be explicitly enabled by a facility admin, never default-on given false-positive risk.

### 2.4 Dashboard / UX (from brief + additions)
- Live Patient Speech Panel / Live English Translation Panel
- Confidence Score Meter (per-sentence + rolling session average)
- Emotion Indicator (per speaker, live)
- Medical Keywords Panel
- Symptoms Panel (running structured list)
- Emergency Alert Card
- Conversation Memory Status (what context the AI is currently tracking — explicit chips, editable/removable by clinician)
- AI Miscommunication Alerts (inline + panel log)
- Consultation Timeline
- AI Consultation Summary (draft, clinician must review/approve before export — **never auto-finalized**)
- Analytics Dashboard (consultation time, speaking ratio, symptom count, avg confidence, emotion trend, accuracy stats)
- Waveform animations (per speaker), modern medical blue/white theme, Dark/Light mode
- **Additional recommended UI elements not in original brief:**
  - Model/latency health indicator (ASR/MT/TTS service status, degraded-mode banner)
  - Manual correction mode for transcript (clinician can fix errors inline; corrections feed a review log, not silently retrain anything without explicit pipeline)
  - Consent & privacy status indicator (recording on/off, camera on/off, data retention countdown)
  - Language/accent selector + "repeat that" quick action
  - Session lock / idle timeout for shared clinical workstations

### 2.5 Platform / Non-Functional Features
- Searchable conversation history, export to PDF/TXT (and JSON for interoperability).
- Secure patient session management, encrypted at rest and in transit.
- Role-based access (Doctor, Patient/Guest, Admin, Auditor).
- Audit log of every AI decision surfaced to a human (immutable, append-only).
- Offline/degraded mode: if translation service is unreachable, fall back to raw bilingual transcript only, clearly labeled "AI assistance unavailable."
- Multi-tenant readiness (per-clinic data isolation) even if v1 ships single-tenant.
- Accessibility: screen-reader labels for all live-updating regions (ARIA live regions), captions always available, high-contrast mode.

---

## 3. Architecture

### 3.1 High-Level System Diagram (textual)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser / PWA)                       │
│  React + TypeScript SPA                                              │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐               │
│  │ Audio Capture │ │ Video Capture │ │ Dashboard UI   │               │
│  │ (WebRTC/Web   │ │ (getUserMedia)│ │ (panels above) │               │
│  │  Audio API)   │ │               │ │                │               │
│  └───────┬───────┘ └───────┬───────┘ └───────▲────────┘               │
│          │  audio chunks    │ frames          │ state (WebSocket)     │
└──────────┼──────────────────┼─────────────────┼──────────────────────┘
           │ WSS               │ WSS (or edge CV)│
┌──────────▼──────────────────▼─────────────────┴──────────────────────┐
│                        API GATEWAY / EDGE (Node.js, Fastify)          │
│   AuthN/Z, rate limiting, WebSocket session mgmt, request routing     │
└──────────┬───────────────────────────────────────────────┬───────────┘
           │                                                │
┌──────────▼───────────┐   ┌──────────────────┐   ┌─────────▼───────────┐
│ Speech Pipeline Svc   │   │ Vision Svc        │   │ Session/Orchestr.   │
│ (Python, FastAPI)     │   │ (Python, FastAPI) │   │ Svc (Node/Python)   │
│ - VAD                 │   │ - Pose estimation │   │ - Conversation      │
│ - Noise suppression   │   │ - Motion analysis │   │   memory store      │
│ - ASR (streaming)     │   │ - Alert rules      │   │ - Session state     │
│ - MT (HI→EN)          │   └──────────────────┘   │ - Event bus pub     │
│ - TTS                 │                            └─────────┬───────┘
│ - Diarization         │                                      │
│ - Emotion classifier  │        ┌─────────────────────────────▼───────┐
└──────────┬────────────┘        │  Clinical NLP Svc (Python, FastAPI)  │
           │                     │  - Medical NER                       │
           │                     │  - Symptom/entity extraction         │
           │                     │  - Risk scoring                      │
           │                     │  - Emergency keyword engine           │
           │                     │  - Miscommunication detector          │
           │                     │  - Summarization (LLM-backed)         │
           │                     └─────────────────────────────┬───────┘
           │                                                    │
┌──────────▼────────────────────────────────────────────────────▼──────┐
│                     Data Layer                                        │
│  PostgreSQL (sessions, transcripts, entities, audit log)              │
│  Redis (live session cache, pub/sub for realtime fan-out)             │
│  Object storage (S3-compatible) — encrypted audio/video snippets       │
│  Vector store (optional, for semantic search over history)            │
└─────────────────────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────────────┐
│         Observability & Safety Layer (cross-cutting)                 │
│  Structured logging, tracing (OpenTelemetry), model-output audit,    │
│  content-safety filters, latency/error alerting, PII redaction       │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow (single utterance)
1. Client streams audio chunks over WebSocket to Speech Pipeline Service.
2. VAD segments speech; noise suppression applied before ASR.
3. Streaming ASR emits partial → final Hindi transcript with confidence.
4. Diarization tags speaker (Patient/Doctor) using channel/voice-print heuristics.
5. Final Hindi transcript → MT service, conditioned on rolling conversation memory (last N turns + structured case memory) for disambiguation.
6. MT output → back-translation check (EN→HI) run in parallel → feeds Miscommunication Detector + Confidence Score.
7. English transcript → TTS → streamed audio to the other party's client.
8. In parallel (async, non-blocking to the speech path): Clinical NLP service runs NER, symptom extraction, risk scoring, emergency keyword scan, emotion classification on the same utterance.
9. Orchestration service merges all outputs, writes to Postgres + Redis, and pushes real-time state to both clients via WebSocket/SSE.
10. Emergency keyword hits short-circuit the pipeline: alert is pushed **immediately** on keyword match, before waiting on the full NLP pass, to minimize latency for critical alerts.

### 3.3 Why this shape
- **Speech path is latency-critical (<1.5s round trip target)** — kept as a lean, dedicated service, not blocked by heavier NLP/summarization work.
- **Clinical NLP path is accuracy-critical, not latency-critical** — allowed to lag by 1–3s without harming conversation flow, since it enriches rather than gates the core exchange (except emergency keywords, which are gated inline for speed).
- **Vision module is isolated** — separate service/process so a CV crash or GPU contention never takes down the audio pipeline.
- **Everything AI-derived is versioned and stored with model name/version + input span reference** for auditability and reproducibility.

---

## 4. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Frontend | React 18 + TypeScript, Vite | Fast iteration, strong typing catches integration bugs early |
| State/data fetching | TanStack Query + Zustand | Predictable realtime state without Redux boilerplate |
| Styling | Tailwind CSS + custom design tokens | Matches "modern medical dashboard" brief fast, themeable for dark/light |
| Realtime transport | WebSocket (native) + fallback SSE | Low-latency bidirectional streaming for audio-adjacent state |
| Audio capture | Web Audio API + MediaStream, Opus encoding | Broad browser support, efficient bandwidth |
| Video/CV client | getUserMedia + on-device pose landmarker (MediaPipe/TF.js) where possible | Reduces PHI video transmission; only derived signals sent to server by default |
| Backend gateway | Node.js (Fastify) | Lightweight, strong WebSocket ecosystem |
| ML services | Python (FastAPI, async) | Native ML ecosystem, easy model swapping |
| ASR | Streaming ASR model (e.g., Whisper-large-v3 fine-tuned for Hindi, or a commercial streaming ASR API) behind an abstraction interface | Swappable; brief needs streaming + accent robustness |
| MT | NLLB/IndicTrans2-class model fine-tuned/prompted with medical glossary, or LLM-based MT with terminology constraints | Domain accuracy for medical terms |
| TTS | Neural TTS (e.g., a streaming-capable English voice model) | Low first-byte latency requirement |
| Emotion | Prosody-feature classifier (openSMILE/torchaudio features) + lightweight classifier head | Explainable, not a black-box end-to-end audio LLM |
| Clinical NLP | spaCy/med7-class NER + curated Hindi-English medical lexicon + LLM-assisted extraction with structured-output constraints | Combines determinism (safety) with LLM flexibility |
| Summarization | LLM (Claude via Anthropic API) with strict structured JSON output + citation back to transcript spans | Matches "explainable AI" principle |
| Pose/motion CV | MediaPipe Pose / BlazePose | Real-time, lightweight, works client-side |
| Database | PostgreSQL 15+ | ACID, mature, good JSONB support for flexible entity storage |
| Cache/pubsub | Redis 7+ | Realtime fan-out, session cache |
| Object storage | S3-compatible (MinIO for local dev) | Encrypted media storage |
| Auth | OAuth2/OIDC + short-lived JWT, MFA for clinical roles | Healthcare-appropriate access control |
| Infra | Docker Compose (dev) → Kubernetes (prod) | Service isolation matches architecture |
| CI/CD | GitHub Actions | Ubiquitous, good ecosystem, matches allowed domains |
| Observability | OpenTelemetry + Prometheus + Grafana, Sentry for errors | Full pipeline tracing across services |
| Testing | Vitest/Jest (frontend), Pytest (Python services), Playwright (E2E) | Standard, well-supported |

---

## 5. Repository File Structure

```
medibridge-ai/
├── docs/
│   ├── BLUEPRINT.md                 # this document
│   ├── AGENT_INSTRUCTIONS.md        # condensed operational rules for Claude Code
│   ├── PROGRESS.md                  # living log, updated every phase
│   ├── ADRs/                        # architecture decision records
│   └── COMPLIANCE.md                # data handling, retention, consent notes
│
├── apps/
│   ├── web/                         # React frontend
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── panels/          # LivePatientPanel, TranslationPanel, etc.
│   │   │   │   ├── alerts/          # EmergencyAlertCard, MisCommAlert
│   │   │   │   ├── charts/          # analytics visualizations
│   │   │   │   └── shared/
│   │   │   ├── hooks/               # useAudioCapture, useSessionSocket, etc.
│   │   │   ├── state/               # zustand stores
│   │   │   ├── services/            # API/WS clients
│   │   │   ├── pages/
│   │   │   ├── theme/               # design tokens, dark/light
│   │   │   └── accessibility/
│   │   ├── tests/
│   │   └── e2e/                     # Playwright specs
│   │
├── services/
│   ├── gateway/                     # Node.js Fastify API gateway
│   │   ├── src/
│   │   │   ├── auth/
│   │   │   ├── ws/
│   │   │   ├── routes/
│   │   │   └── middleware/
│   │   └── tests/
│   │
│   ├── speech-pipeline/             # Python FastAPI
│   │   ├── app/
│   │   │   ├── asr/
│   │   │   ├── mt/
│   │   │   ├── tts/
│   │   │   ├── diarization/
│   │   │   ├── noise_suppression/
│   │   │   ├── emotion/
│   │   │   └── confidence/
│   │   └── tests/
│   │
│   ├── clinical-nlp/                # Python FastAPI
│   │   ├── app/
│   │   │   ├── ner/
│   │   │   ├── symptom_extraction/
│   │   │   ├── risk_scoring/
│   │   │   ├── emergency_detector/
│   │   │   ├── miscommunication/
│   │   │   ├── summarization/
│   │   │   └── lexicons/            # medical term dictionaries, versioned
│   │   └── tests/
│   │
│   ├── vision-service/               # Python FastAPI
│   │   ├── app/
│   │   │   ├── pose/
│   │   │   ├── collapse_detection/
│   │   │   ├── frame_exit_detection/
│   │   │   └── stillness_detection/
│   │   └── tests/
│   │
│   └── orchestrator/                 # Session/state orchestration
│       ├── app/
│       │   ├── session/
│       │   ├── memory/               # conversation memory store logic
│       │   ├── audit/
│       │   └── events/
│       └── tests/
│
├── packages/
│   ├── shared-types/                 # TS + Python schema parity (OpenAPI/JSON Schema generated)
│   ├── medical-lexicon/              # shared Hindi/English medical term data
│   └── design-tokens/
│
├── infra/
│   ├── docker/
│   │   ├── docker-compose.dev.yml
│   │   └── Dockerfile.*
│   ├── k8s/
│   │   ├── base/
│   │   └── overlays/{dev,staging,prod}/
│   └── terraform/                    # optional, cloud infra as code
│
├── .github/
│   └── workflows/
│       ├── ci-web.yml
│       ├── ci-services.yml
│       ├── ci-e2e.yml
│       ├── security-scan.yml
│       └── deploy.yml
│
├── scripts/
│   ├── setup-dev.sh
│   ├── seed-test-data.py
│   └── model-eval/                   # offline eval harnesses for ASR/MT/NER
│
├── .env.example
├── README.md
└── LICENSE
```

---

## 6. Development Constraints

### 6.1 Hard Constraints
- **No PHI (Protected Health Information) leaves the system unencrypted**, at rest or in transit — TLS everywhere, AES-256 at rest.
- **No third-party model call may retain data by default** — use providers/configurations with zero-retention or self-hosted models for anything touching raw patient audio/video. Document any exception explicitly in `COMPLIANCE.md`.
- **Camera is opt-in per session**, off by default, with a persistent on-screen recording indicator whenever active.
- **No feature may auto-page emergency services or clinical staff without explicit facility-level configuration** — the system alerts *in-app* by default; escalation integrations are opt-in infrastructure, not default behavior.
- **All AI-generated clinical content (summary, risk level, entities) must be labeled AI-generated and require clinician acknowledgment before being treated as part of the record.**
- Every service must degrade gracefully — no single ML service outage can crash the session; the UI must clearly show which capabilities are degraded.
- Latency budget: ASR partials <300ms, full utterance round-trip (speech-in → translated speech-out) <1.5s p95, emergency keyword alert <500ms from ASR final.

### 6.2 Development Process Constraints (for the coding agent)
- Work in vertical slices per Section 8 phase — do not scaffold all services simultaneously without tests.
- Every new module ships with unit tests in the same PR/commit; no "add tests later."
- No hardcoded secrets/API keys — `.env` + secret manager only, `.env.example` kept in sync.
- All AI/ML model interfaces must sit behind an abstraction (interface/adapter), so ASR/MT/TTS/LLM providers are swappable without touching business logic.
- Any new dependency must be justified in the commit message (why, alternatives considered) if it materially changes the stack in Section 4.
- Type safety enforced: TS strict mode on frontend; mypy/pydantic strict on Python services.
- No feature is "done" until it has: unit tests, an integration test where relevant, and an update to `PROGRESS.md`.

---

## 7. Edge Cases

### 7.1 Speech & Language
- Silence / no speech detected for extended period.
- Overlapping speech (both patient and doctor talk simultaneously) — diarization ambiguity.
- Code-switching mid-sentence (Hindi-English mixed, common in Indian clinical settings).
- Regional Hindi dialects/accents with low ASR confidence.
- Non-Hindi language spoken by mistake (Tamil, Bengali, English-only patient) — must detect and prompt, not silently mistranslate.
- Extremely fast or extremely slow speech.
- Whispered speech (patient in pain, low volume) vs shouting.
- Medical jargon spoken by doctor, colloquial/folk terms spoken by patient describing the same symptom (e.g., regional terms for jaundice) — lexicon must map both.
- Negation and hedging: "no fever," "maybe some dizziness," "not sure if it's chest pain" — must not be flattened to positive symptom mentions.
- Numbers/dosages misheard (e.g., "500mg" vs "50mg") — flagged as high-risk ambiguity requiring confirmation, never silently passed through.
- Sarcasm/idiom that doesn't map to literal medical meaning.

### 7.2 System / Network
- Network drop mid-session — must resume without losing conversation memory, with a visible "reconnecting" state.
- ASR/MT/TTS provider outage or rate-limit — graceful fallback to raw transcript-only mode.
- Extreme background noise exceeding suppression capability — UI must warn rather than emit garbage translations.
- Microphone/camera permission denied or revoked mid-session.
- Multiple browser tabs/devices for the same session.
- Clock skew between client and server affecting timestamp ordering.

### 7.3 Clinical / Safety
- Emergency keyword detected but immediately retracted/corrected by speaker ("chest pain — no wait, I meant no chest pain") — must re-evaluate, not leave a stale alert, but must log both states.
- Conflicting information across the session (patient says "no allergies" early, then mentions a drug allergy later) — memory module must surface the conflict, not silently overwrite.
- Emotion classifier misreads culturally different expressiveness norms as distress — confidence and disclaimer must prevent overconfident display.
- Risk-level flip-flopping rapidly due to noisy per-utterance scoring — must use hysteresis/smoothing, not instant flips that alarm-fatigue the clinician.
- Vision module false positive (patient bent down to tie shoe reads as "collapse") — require multi-frame confirmation before alerting.
- Patient or doctor deliberately tests the system with false emergency phrases — system should still alert (safety-first) but this is a known limitation to document, not something to "cleverly" suppress.

### 7.4 Data / Privacy
- Session ends abruptly (browser closed) — ensure partial data is saved/flushed, not lost or left in a corrupt state.
- Export requested mid-session vs after session close.
- Right-to-deletion / retention policy expiry while data is referenced in an active audit trail.
- Two patients sharing one workstation sequentially — session isolation and forced logout.

---

## 8. Agentic Build Roadmap (Phased, for Claude Code)

Each phase = one or more PRs, ends with tests green and `PROGRESS.md` updated. Do not proceed to next phase until current phase's Definition of Done (Section 10) is met.

**Phase 0 — Foundations**
Repo scaffold (Section 5), CI skeleton, Docker Compose dev environment, shared type/schema package, design tokens, basic auth stub, empty service health-check endpoints.

**Phase 1 — Core Speech Pipeline (text-only, no UI polish)**
Audio capture → ASR (streaming, Hindi) → raw transcript over WebSocket. Test with pre-recorded Hindi audio fixtures before live mic. Latency instrumentation from day one.

**Phase 2 — Translation + TTS**
MT service (HI→EN) wired to Phase 1 output; TTS output streamed back; confidence scoring v1 (ASR confidence only, MT self-consistency added next).

**Phase 3 — Bilingual Transcript UI + Speaker Diarization**
Dashboard shell (blue/white theme, panels layout), live bilingual transcript with timestamps, diarization integrated, waveform animation.

**Phase 4 — Conversation Memory + Miscommunication Detector**
Rolling context + structured case memory; back-translation consistency check; confidence score v2 (composite); miscommunication alert UI.

**Phase 5 — Clinical NLP: NER, Symptom Extraction, Keyword Highlighting**
Lexicon-backed extraction, entity categorization panel, inline keyword highlighting with tooltips.

**Phase 6 — Risk, Emergency Detection, Emotion**
Risk-level classifier with hysteresis, emergency keyword engine with <500ms alert path, emotion classifier + indicator UI, alarm-fatigue safeguards.

**Phase 7 — Summary, Timeline, Analytics**
LLM-backed structured summary with span citations + clinician-approval gate, timeline generator, analytics dashboard (session stats).

**Phase 8 — Vision/CV Module**
Consent flow, pose-based collapse/motionlessness/frame-exit detection, multi-frame confirmation logic, emergency notification integration (in-app only by default).

**Phase 9 — Platform Hardening**
RBAC, audit log, encryption at rest/in transit verification, export (PDF/TXT/JSON), searchable history, session security (idle timeout, lock), dark/light mode polish, accessibility pass.

**Phase 10 — Resilience & Chaos**
Fault injection for each edge case in Section 7 (network drop, provider outage, overlapping speech, etc.), degraded-mode verification, load testing.

**Phase 11 — Release Readiness**
Full E2E suite, security scan clean, performance budget met, `COMPLIANCE.md` finalized, staged rollout plan.

---

## 9. Condensed Agent Operating Rules (for `AGENT_INSTRUCTIONS.md`)

1. Read `PROGRESS.md` first, every session, before writing code.
2. Work only within the current phase's scope (Section 8) unless explicitly redirected.
3. Never mark a task done without a passing test proving it.
4. Never silently swallow an ML service error — surface it to the UI state.
5. Never let a "confidence" or "risk" number appear in the UI without its underlying reason string attached.
6. Ask before introducing a new external API/service dependency not already in Section 4.
7. After each phase: run full test suite, update `PROGRESS.md` with what changed, what passed, what's deferred, then commit.
8. If a requirement is ambiguous, make the safety-conservative choice (e.g., prefer alerting over staying silent) and note the assumption in the PR description.

---

## 10. Definition of Done / Completion Goals (Verified Against Test Results)

A phase or feature is **only** complete when all of the following are true — not when code merely runs:

| Gate | Requirement |
|---|---|
| Unit tests | ≥90% coverage on new logic; all green |
| Integration tests | Service-to-service contract verified (e.g., speech-pipeline → orchestrator schema match) |
| E2E test | At least one Playwright scenario exercises the feature end-to-end through the UI |
| Latency budget | Feature does not regress p95 latency budgets in Section 6.1 (verified via CI perf check) |
| Edge cases | Relevant edge cases from Section 7 have explicit test cases (Section 12) marked passing |
| Explainability | Any AI-derived value shown in UI has a "why" surfaced (rule fired / model + confidence) |
| Fail-safe check | Killing the responsible service mid-session produces a graceful degraded state, not a crash — verified by chaos test |
| Security scan | No new high/critical findings from CI security scan (Section 13) |
| Docs | `PROGRESS.md` and relevant ADR updated |
| Human review checkpoint | For clinical-facing features (risk, emergency, summary): a documented manual review against the sample test-case transcripts in Section 12.3 |

Overall **v1 completion** is defined as: all Phase 0–9 gates green, Phase 10 chaos suite passing with no unhandled crashes, and Phase 11 checklist fully signed off.

---

## 11. Hallucination & Error Safeguards

This is the most important section for a system touching medical communication. Concrete mechanisms, not just principles:

### 11.1 Structural Safeguards
- **Grounding via span citation**: every extracted entity, symptom, and summary bullet must carry a reference to the exact transcript span it came from. If an LLM-based extractor cannot produce a valid span match, the item is discarded, not shown.
- **Constrained generation for structured outputs**: summarization and entity extraction use schema-constrained/JSON-mode generation rather than free text, rejecting and retrying outputs that don't validate against the schema.
- **Dual-path verification for translation**: back-translation (EN→HI) compared against original HI via semantic similarity; large divergence auto-downgrades confidence to Red and flags miscommunication rather than presenting a confident-looking but possibly wrong translation.
- **Deterministic lexicon backstop**: safety-critical terms (drug names, negations, emergency phrases) are matched against a curated deterministic lexicon in parallel with the ML pipeline. On disagreement between the lexicon and the model, the more conservative (safety-favoring) interpretation wins and both are logged.
- **No numeric fabrication**: dosages, vitals, and other numbers are never "smoothed" or auto-corrected by the LLM; if ASR confidence on a number is low, the UI asks for confirmation rather than guessing.

### 11.2 Runtime Safeguards
- Confidence thresholds gate what's shown as fact vs. what's shown as "uncertain — please confirm."
- Rate-limited re-scoring with hysteresis prevents flapping risk levels / repeated emergency banners from noisy single utterances.
- Every AI-generated clinical artifact (summary, entity list) is versioned and diffable — clinician edits are tracked separately from AI output, never merged silently.
- Circuit breakers around every external model call; on repeated failure, the system flips to "AI assistance degraded" mode automatically and visibly.

### 11.3 Evaluation Safeguards
- Offline eval harness (`scripts/model-eval/`) runs ASR WER, MT BLEU/COMET + medical-term accuracy, NER precision/recall, and emergency-keyword recall against a held-out labeled test set **before** any model/prompt change ships.
- Regression gate in CI: a model/prompt change that drops medical-term MT accuracy or emergency-keyword recall below a defined floor blocks merge automatically.
- Human-labeled "gold set" of Hindi medical consultation transcripts (synthetic + anonymized/consented where possible) used for periodic manual audit, not just automated metrics.

### 11.4 Product-Level Safeguards
- Persistent, non-dismissible-without-acknowledgment disclaimer: "MediBridge AI assists communication. It does not diagnose. Always confirm critical information verbally."
- Emergency alerts always favor false positives over false negatives, but every false-positive dismissal is logged and reviewable to tune thresholds over time without ever loosening the emergency-keyword list itself.

---

## 12. Test Cases

### 12.1 Unit-Level (representative, not exhaustive)
- ASR: given known audio fixture, transcript matches expected within WER threshold.
- MT: given Hindi medical sentence with negation, English output preserves negation.
- Confidence scorer: given deliberately mismatched back-translation, score lands in Red band.
- Emergency detector: given each phrase in the trigger list (and paraphrases), alert fires within latency budget.
- Emergency detector negative case: given clearly unrelated speech containing a trigger word in non-medical context ("chest of drawers"), verify behavior is documented (accept conservative false positive, or confirm contextual disambiguation works — whichever is chosen, must be explicitly tested).
- Risk scorer: given symptom set escalating over 3 turns, verify hysteresis prevents single-turn flip, but verify it does escalate appropriately over sustained evidence.
- Entity extractor: given a sentence with a medicine name misspelled/mispronounced, verify fuzzy-match against lexicon still finds a candidate with lower confidence, not silently dropped.

### 12.2 Integration-Level
- Full round trip: mic input (fixture) → orchestrator emits final state with transcript, translation, confidence, entities, risk level, all schema-valid.
- Session reconnect: kill WebSocket mid-utterance, reconnect, verify conversation memory and transcript continuity preserved.
- Service outage: kill MT service, verify system falls back to raw transcript mode and UI shows degraded banner, verify TTS/ASR unaffected.
- Multi-service race: emergency keyword fires simultaneously with a low ASR confidence score — verify alert still fires (safety path is not gated by general confidence).

### 12.3 Clinical Scenario Test Transcripts (for human review checkpoint, Section 10)
Maintain a fixed set of scripted bilingual consultation transcripts covering:
1. Routine consultation, no red flags — verify no false emergency alerts, accurate summary.
2. Chest pain with radiating arm pain — verify emergency banner + correct risk escalation.
3. Patient with conflicting statements about allergies — verify conflict surfaced, not silently overwritten.
4. Heavily accented/noisy audio sample — verify degraded-confidence handling, no fabricated high-confidence translation.
5. Code-switched Hindi-English sentence — verify correct handling without garbling.
6. Patient becomes distressed mid-conversation — verify emotion indicator updates and risk score reflects it appropriately without overreacting to a single moment.
7. False-alarm CV scenario (patient bends to pick up dropped item) — verify multi-frame confirmation prevents premature collapse alert.
8. Genuine motionlessness scenario (simulated) — verify collapse/motionlessness alert fires within threshold.

### 12.4 E2E (Playwright)
- Full session: login → start consultation → speak → see live bilingual transcript → end session → view summary → export PDF.
- Accessibility pass: keyboard-only navigation through all panels, screen reader announces live transcript updates and emergency alerts.
- Dark/light mode toggle persists across session and reload.

### 12.5 Non-Functional
- Load test: N concurrent sessions, verify p95 latency budgets hold (Section 6.1).
- Security: dependency vulnerability scan, auth bypass attempts, WebSocket message fuzzing.
- Data retention: verify scheduled deletion job removes data past retention window and audit log reflects the deletion event itself.

---

## 13. CI/CD Defenses

### 13.1 Pipeline Stages (GitHub Actions)
1. **Lint & type-check** — ESLint/Prettier (web), Ruff/mypy (Python) — blocks on failure.
2. **Unit tests** — per-service, parallelized, coverage report uploaded, minimum threshold enforced (fails build below 90% on new/changed code).
3. **Integration tests** — spin up Docker Compose stack, run cross-service contract tests.
4. **Model regression eval** — run `scripts/model-eval/` against gold set; block merge if key metrics (medical-term MT accuracy, emergency-keyword recall, NER F1) regress beyond defined tolerance.
5. **Security scan** — dependency CVE scan (e.g., `npm audit`, `pip-audit`), static analysis (Semgrep/Bandit), secret scanning (gitleaks) on every PR.
6. **E2E suite** — Playwright against a staging-like ephemeral environment, nightly + pre-release.
7. **Performance budget check** — latency benchmarks against Section 6.1 budgets; fails build on regression beyond threshold.
8. **Chaos/resilience suite** — scheduled (not every PR, to save cost) — kills services mid-session and asserts graceful degradation.
9. **Build & containerize** — multi-stage Docker builds, image scanning (Trivy) before push.
10. **Deploy** — staged rollout (dev → staging → prod), automated rollback on health-check/error-rate regression post-deploy.

### 13.2 Branch Protections
- No direct pushes to `main`; PR + at least one review (or Claude Code self-review checklist documented in PR description) + all CI gates green required.
- `main` is always deployable; feature work happens on short-lived branches per Phase/sub-feature.
- Required status checks: lint, unit, integration, security scan, model regression eval.

### 13.3 Release Gates
- No release ships with a Red/failing state in Section 10's Definition of Done table.
- Release notes must explicitly state any known limitations (e.g., "Emotion detection not validated across all regional accents yet") — no silent scope narrowing.

---

## 14. Compliance & Data Handling Notes (summary — full detail in `COMPLIANCE.md`)

- Treat all session data as sensitive health information regardless of jurisdiction; apply strictest reasonable standard (e.g., HIPAA-aligned technical safeguards: encryption, access controls, audit logging, minimum necessary access) as a baseline even if not formally certifying compliance in v1.
- Explicit informed consent screen before recording starts (audio) and before camera activates (video), each independently toggleable and revocable mid-session.
- Data minimization: raw audio/video retained only as long as configured retention policy requires; derived transcripts/entities can be retained longer under separate policy since they carry different risk profiles — document both clearly.
- Clear separation between "AI-assisted draft" data and "clinician-confirmed" data in the schema, so exports and audits can distinguish provenance at all times.

---

## 15. Summary

MediBridge AI's real risk isn't "can we build all these AI features" — it's **can we build them so that every AI output is traceable, explainable, and safely overridable by a human**, in a domain where a wrong or overconfident answer has real consequences. This blueprint is structured so that the agentic build process (Sections 8–10) enforces that discipline at every phase, not just at the end: every feature ships with tests, every AI claim ships with a "why," and every failure mode has a defined, tested, graceful fallback rather than an undefined one.
