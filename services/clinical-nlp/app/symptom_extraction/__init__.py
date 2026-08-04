"""Symptom extraction is not a separate pipeline from app.ner -- Blueprint
Section 2.2 describes it as "NER + curated lexicon, normalized to canonical
codes," which is exactly what app.ner.extractor already does. Symptoms are
simply entities where category == "symptom"; building a second parallel
extraction path here would duplicate that logic for no benefit. This
package stays a placeholder intentionally."""

