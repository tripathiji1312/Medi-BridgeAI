# COMPLIANCE.md
### Data handling, retention, and consent — full detail (summary lives in BLUEPRINT.md Section 14)

**Status:** Draft skeleton created in Phase 0. Must be filled in and re-reviewed before Phase 11
(Release Readiness) sign-off. Nothing in this document authorizes production handling of real
patient data until every section below is completed and reviewed.

---

## 1. Data Classification

All session data (audio, video, transcripts, derived entities, summaries) is treated as sensitive
health information regardless of jurisdiction. Baseline technical safeguards are applied even
though v1 does not formally certify HIPAA/any specific regime:
- Encryption in transit: TLS 1.2+ everywhere.
- Encryption at rest: AES-256 for object storage (audio/video) and database-level encryption for
  Postgres.
- Access controls: role-based (Doctor, Patient/Guest, Admin, Auditor) — see `services/gateway/src/auth`.
- Audit logging: append-only, every AI decision surfaced to a human is logged (`services/orchestrator/app/audit`).
- Minimum necessary access: to be enforced per-role once RBAC lands (Phase 9).

## 2. Consent

- Recording (audio) requires explicit informed consent before capture starts.
- Camera (video/CV module) requires a **separate, independently revocable** consent, off by
  default, with a persistent on-screen indicator whenever active (Blueprint Section 6.1, 2.3).
- Both toggles must be revocable mid-session without ending the clinical session itself.
- Consent UI implementation: Phase 8 (Vision/CV Module) and Phase 9 (Platform Hardening).

## 3. Retention

- Raw audio/video: retained only as long as the configured retention policy requires (policy
  value TBD — facility-configurable, default to be set conservatively before any pilot).
- Derived transcripts/entities: may be retained longer under a **separate** policy, since they
  carry a different (lower, but still sensitive) risk profile than raw media.
- Deletion jobs must be logged in the audit trail — the deletion event itself is an auditable
  fact (Blueprint Section 7.4, 12.5).
- Right-to-deletion requests that touch data referenced by an active audit trail: the audit
  record of "this data existed and was deleted" survives; the underlying PHI does not. (Edge
  case flagged in Blueprint Section 7.4 — implementation deferred to Phase 9/11.)

## 4. Provenance Separation

- Every export/audit view must be able to distinguish "AI-assisted draft" from
  "clinician-confirmed" data at all times (Blueprint Section 14, `AGENT_INSTRUCTIONS.md` Rule 5).
- Enforced at the schema level once `packages/shared-types` grows the relevant contracts
  (Phase 4+ for conversation memory / entities, Phase 7 for summaries).

## 5. Third-Party Model Calls

- No third-party model call may retain data by default. Any provider used for raw patient
  audio/video must offer zero-retention or be self-hosted.
- **Any exception must be listed here explicitly before it ships:**

| Provider | Data touched | Retention behavior | Justification | Approved? |
|---|---|---|---|---|
| _(none yet — Phase 0 has no live model calls)_ | | | | |

## 6. Open Items Before Production Pilot

- [ ] Finalize retention window values with a facility/legal stakeholder.
- [ ] Confirm encryption-at-rest configuration for the chosen Postgres/object-storage deployment.
- [ ] Complete RBAC + MFA (Phase 9) before any real patient data is used.
- [ ] Legal review of this document.
