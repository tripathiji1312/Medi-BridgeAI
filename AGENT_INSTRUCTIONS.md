# AGENT_INSTRUCTIONS.md
### Operational rules for Claude Code — read this at the start of every session, before writing any code.

This file is the durable memory substitute across sessions. It does not replace `docs/BLUEPRINT.md` — it's the condensed, action-oriented checklist derived from it. If anything here conflicts with the blueprint, the blueprint wins; update this file to match, don't silently diverge.

---

## 0. Session Start Checklist (do this every time, in order)

1. Read `docs/PROGRESS.md` in full. Identify: current phase, last completed task, any "deferred" or "known issue" notes.
2. Read the relevant phase section in `docs/BLUEPRINT.md` (Section 8) for what's in scope right now.
3. Run the existing test suite before changing anything. If it's not green, fixing that is the first task — do not build on top of a red suite.
4. Confirm which service(s) you're touching this session and scope your work to that boundary (see Section 2 below).
5. Only after 1–4: start work.

---

## 1. Scope Discipline

- Work **one phase at a time**, per `BLUEPRINT.md` Section 8. Do not jump ahead to build Phase 6 features while Phase 3 is incomplete, even if it seems efficient.
- Work in **vertical slices**: a feature isn't "started" until there's a path from input → output → test, even a minimal one. Don't scaffold five empty services before any one of them does something real.
- If a task feels like it needs a new external dependency, model provider, or architectural change not already in `BLUEPRINT.md` Section 4, **stop and flag it** in your response rather than silently adding it.
- If a requirement is ambiguous, resolve it toward the **safety-conservative** choice (favor alerting over silence, favor flagging uncertainty over guessing) and write down the assumption you made.

---

## 2. Service Boundaries (don't blur these)

| Service | Owns | Must NOT do |
|---|---|---|
| `apps/web` | UI, client state, audio/video capture | Business logic, model inference |
| `services/gateway` | Auth, routing, WS session mgmt | ML inference, clinical logic |
| `services/speech-pipeline` | ASR, MT, TTS, diarization, noise suppression, emotion | Symptom/entity extraction, risk scoring |
| `services/clinical-nlp` | NER, symptom extraction, risk scoring, emergency detection, miscommunication detection, summarization | Audio/video processing |
| `services/vision-service` | Pose/motion/collapse detection | Anything audio-related |
| `services/orchestrator` | Session state, conversation memory, audit log, event fan-out | Direct ML inference |

If a change seems to require crossing one of these boundaries, that's a signal to route through an event/API contract, not to reach across and call another service's internals directly.

---

## 3. Non-Negotiable Rules (apply regardless of phase)

1. **Every AI-derived value shown in the UI carries its "why."** Confidence score, risk level, emotion, emergency alert — none of these render without a reason string or source span attached. No exceptions, no "add explainability later."
2. **No silent fallback.** If a model/service call fails or degrades, the UI must show a degraded-state indicator. Never quietly serve stale or fabricated data as if it were fresh and confident.
3. **No numeric fabrication.** Dosages, vitals, timestamps — if ASR/extraction confidence is low, surface "please confirm," don't auto-correct or smooth the number.
4. **Emergency detection is safety-first.** When in doubt, alert. False positives are acceptable and logged for tuning; false negatives are not acceptable trade-offs to "reduce noise."
5. **AI-generated clinical content is a draft until a clinician acknowledges it.** Summaries, risk levels, entity lists — store and label AI output separately from clinician-confirmed data. Never merge them silently.
6. **No PHI leaves the system unencrypted.** TLS in transit, AES-256 at rest, always — this applies to test fixtures containing realistic-looking data too; use synthetic/anonymized data for local dev and tests.
7. **Camera is opt-in, per session, revocable mid-session**, with a persistent on-screen recording indicator whenever active. Never default it on.
8. **Every new module ships with tests in the same commit.** "Add tests later" is not an acceptable PR state.

---

## 4. Definition of Done (copy from BLUEPRINT.md Section 10 — check every item before calling something complete)

- [ ] Unit tests written and passing, ≥90% coverage on new/changed logic
- [ ] Integration test covers the service-to-service contract, if applicable
- [ ] At least one E2E scenario exercises the feature through the UI, if user-facing
- [ ] Feature does not regress latency budgets (ASR partial <300ms, full round-trip <1.5s p95, emergency alert <500ms)
- [ ] Relevant edge cases from `BLUEPRINT.md` Section 7 have explicit test coverage
- [ ] Any AI-derived UI value has a visible reason/source attached
- [ ] Killing the responsible service mid-session degrades gracefully (manually verified or chaos-tested)
- [ ] No new high/critical findings from security scan
- [ ] `docs/PROGRESS.md` updated
- [ ] For clinical-facing features specifically: checked against the scripted test transcripts in `BLUEPRINT.md` Section 12.3

Do not mark a task complete in `PROGRESS.md` unless every applicable box above is genuinely checked — not "should be fine."

---

## 5. End-of-Session Checklist

1. Run the full test suite one more time. It must be green (or you must clearly document what's red and why in `PROGRESS.md`).
2. Update `docs/PROGRESS.md`:
   - What changed this session
   - What tests were added/passed
   - What's deferred, and why
   - Any assumptions made on ambiguous requirements
   - Next recommended task
3. Commit with a message that states *what* and *why*, not just *what*.
4. If you introduced any deviation from `BLUEPRINT.md` (new dependency, changed architecture, changed scope), note it explicitly so the blueprint can be updated — don't let the docs silently go stale.

---

## 6. When Something Feels Ambiguous or Risky

Stop and surface it rather than guessing silently, especially for:
- Anything touching emergency detection thresholds or logic
- Anything touching data retention/deletion
- Anything that would change what's shown to a clinician as "confirmed" vs "AI draft"
- Any new external API/model call handling patient audio, video, or transcript data

Default answer when uncertain: **the more conservative, more explainable, more human-overridable option wins.**
