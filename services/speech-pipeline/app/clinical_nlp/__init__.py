"""Client for clinical-nlp's HTTP API. speech-pipeline computes translation
and back-translation (pure MT); clinical-nlp judges consistency between
them -- this package is the API contract that crosses that service
boundary correctly (AGENT_INSTRUCTIONS.md Section 2), not a place for
clinical logic itself."""
