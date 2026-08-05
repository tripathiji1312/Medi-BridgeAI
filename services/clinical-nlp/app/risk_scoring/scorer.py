"""Single-utterance risk scoring (Blueprint Section 2.2: "Low/Medium/High
classifier using symptom set + emergency keyword match + emotion signal,
always shown with the rule or model reason"). Deterministic rules over the
same lexicon-matching engine used for entity extraction and emergency
detection -- no ML model, so there's nothing here that can't be traced back
to an exact rule.

Stateless and turn-agnostic by design: this only ever sees one utterance in
isolation. Turning a sequence of these into the smoothed level actually
shown to the clinician is app.risk_scoring.hysteresis's job -- kept separate so the
scoring rule and the anti-flapping logic can be tested (and reasoned about)
independently.
"""

from __future__ import annotations

from app.emergency_detector.detector import build_reason, detect_emergency
from app.lexicons.loader import MedicalLexicon
from app.ner.extractor import extract_entities
from app.risk_scoring.schemas import EmotionCategory, RiskLevel

# Emotions that, alongside at least one symptom mention, escalate a
# borderline case from Low to Medium. Not "angry" -- anger doesn't by itself
# suggest clinical risk the way fear/stress/anxiety about one's own
# symptoms does; conflating them would be an unfounded assumption.
CONCERNING_EMOTIONS: frozenset[EmotionCategory] = frozenset({"fearful", "stressed", "anxious"})

# Below this confidence, the emotion signal is too uncertain to let it
# influence risk level on its own -- same "don't let a low-confidence signal
# silently drive a high-stakes decision" principle as everywhere else in
# this build. Not tuned against a labeled gold set; qualitative starting
# point, same caveat as every other threshold introduced so far.
EMOTION_CONFIDENCE_FLOOR = 0.5

MEDIUM_SYMPTOM_COUNT = 2


def compute_raw_risk(
    text: str,
    lexicon: MedicalLexicon,
    emotion_label: EmotionCategory | None,
    emotion_confidence: float | None,
) -> tuple[RiskLevel, str, int, bool]:
    """Returns (raw_level, reason, symptom_count, emergency_triggered)."""
    emergency_matches = detect_emergency(text, lexicon)
    symptom_entities = [e for e in extract_entities(text, lexicon) if e.category == "symptom"]
    symptom_count = len(symptom_entities)

    if emergency_matches:
        reason = build_reason(emergency_matches) or "Emergency keyword detected."
        return "high", reason, symptom_count, True

    concerning_emotion = (
        emotion_label in CONCERNING_EMOTIONS
        and emotion_confidence is not None
        and emotion_confidence >= EMOTION_CONFIDENCE_FLOOR
    )

    if symptom_count >= MEDIUM_SYMPTOM_COUNT or (symptom_count >= 1 and concerning_emotion):
        parts: list[str] = []
        if symptom_count > 0:
            names = ", ".join(sorted({e.canonical_name for e in symptom_entities}))
            parts.append(f"{symptom_count} symptom(s) mentioned ({names})")
        if concerning_emotion:
            assert emotion_confidence is not None
            parts.append(f"tone assessed as {emotion_label} ({round(emotion_confidence * 100)}% confidence)")
        return "medium", "; ".join(parts) + ".", symptom_count, False

    if symptom_count == 1:
        return "low", f"1 symptom mentioned ({symptom_entities[0].canonical_name}), no other risk signals.", 1, False

    return "low", "No symptoms or risk signals detected in this utterance.", 0, False
