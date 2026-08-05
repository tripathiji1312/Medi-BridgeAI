"""Per-session risk-level smoothing (Blueprint Section 7.3: "Risk-level
flip-flopping rapidly due to noisy per-utterance scoring -- must use
hysteresis/smoothing, not instant flips that alarm-fatigue the clinician").

This is internal working memory for clinical-nlp's own risk-scoring
algorithm, not general conversation state -- that's orchestrator's job
(AGENT_INSTRUCTIONS.md Section 2). Kept here, in-process, scoped to just
"the last couple of raw risk observations per session", because it's an
implementation detail of one algorithm's smoothing, not something any other
service or feature needs to read. Same in-process-dict-is-adequate
rationale as orchestrator.app.memory.store.MemoryStore -- not persisted
across restarts; multi-instance persistence is Phase 9 infra hardening,
out of scope here.

An emergency-triggered "high" always overrides the smoothing immediately
(Blueprint Section 12.2's "emergency keyword fires simultaneously with a
low ASR confidence score -- verify alert still fires [...] safety path is
not gated by general confidence" extends here too): a real emergency
keyword match is never held back waiting for a second confirming turn.

Escalation and de-escalation both require two consecutive raw observations
at the new level before the *displayed* level actually changes -- this is
what prevents a single noisy utterance from flipping the badge, while still
letting a genuinely sustained trend (Blueprint Section 12.1: "symptom set
escalating over 3 turns... verify it does escalate appropriately over
sustained evidence") come through.
"""

from __future__ import annotations

from app.risk_scoring.schemas import RiskLevel

_CONFIRMATION_TURNS = 2


class _SessionHysteresis:
    def __init__(self) -> None:
        self.displayed_level: RiskLevel | None = None
        self._pending_level: RiskLevel | None = None
        self._pending_count = 0

    def step(self, raw_level: RiskLevel, emergency_triggered: bool) -> RiskLevel:
        if emergency_triggered:
            self.displayed_level = "high"
            self._pending_level = None
            self._pending_count = 0
            return self.displayed_level

        if self.displayed_level is None:
            self.displayed_level = raw_level
            return self.displayed_level

        if raw_level == self.displayed_level:
            self._pending_level = None
            self._pending_count = 0
            return self.displayed_level

        if raw_level == self._pending_level:
            self._pending_count += 1
        else:
            self._pending_level = raw_level
            self._pending_count = 1

        if self._pending_count >= _CONFIRMATION_TURNS:
            self.displayed_level = raw_level
            self._pending_level = None
            self._pending_count = 0

        return self.displayed_level


class RiskHistoryStore:
    def __init__(self) -> None:
        self._sessions: dict[str, _SessionHysteresis] = {}

    def step(self, session_id: str, raw_level: RiskLevel, emergency_triggered: bool) -> RiskLevel:
        if session_id not in self._sessions:
            self._sessions[session_id] = _SessionHysteresis()
        return self._sessions[session_id].step(raw_level, emergency_triggered)

    def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
