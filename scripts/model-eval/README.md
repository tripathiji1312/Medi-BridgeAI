# Offline Model Evaluation Harness

Per `docs/BLUEPRINT.md` Section 11.3 / 13.1 stage 4: runs ASR WER, MT BLEU/COMET + medical-term
accuracy, NER precision/recall, and emergency-keyword recall against a held-out labeled gold set
**before** any model/prompt change ships. A regression below the defined floor blocks merge.

**Phase 0 status:** directory placeholder only. There is no model integration yet to evaluate
(Phase 1 introduces ASR). Populate with:
- `gold_set/` — held-out labeled Hindi medical consultation transcripts (synthetic/anonymized).
- `eval_asr.py`, `eval_mt.py`, `eval_ner.py`, `eval_emergency_keywords.py` — one script per metric.
- `thresholds.yaml` — the regression-gate floor values referenced by `ci-services.yml`.

Do not add these until the corresponding pipeline phase (Blueprint Section 8) lands the model
they evaluate — an eval harness with nothing real to evaluate against is scope creep.
