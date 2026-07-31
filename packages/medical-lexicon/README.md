# @medibridge/medical-lexicon

Curated Hindi/English medical term lexicon (Blueprint Section 2.2, 4, 11.1 — "deterministic
lexicon backstop"). Backs symptom extraction, medical keyword highlighting, and the
emergency-keyword engine.

**Phase 0 status:** empty, versioned stub only. Real lexicon content (ICD-10/SNOMED-mapped
symptom terms, colloquial/folk term mappings, emergency trigger phrases, drug names) is
**Phase 5/6 scope** — do not populate ahead of that phase.

## Schema (`lexicon.v1.json`)

```jsonc
{
  "version": "0.0.0",
  "terms": [
    // { "canonical": "chest_pain", "hindi": ["सीने में दर्द"], "english": ["chest pain"],
    //   "category": "symptom", "icd10": "R07.9", "isEmergencyKeyword": true }
  ]
}
```

`version` follows semver and is bumped on any content change — every extracted entity in the
running system references the lexicon version it was matched against, for auditability
(Blueprint Section 3.3: "everything AI-derived is versioned").
