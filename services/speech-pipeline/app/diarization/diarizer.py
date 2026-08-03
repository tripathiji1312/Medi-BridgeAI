"""Stateful, per-session online speaker clustering on top of real ECAPA-TDNN
embeddings. One instance per WebSocket connection, mirroring
StreamingASRSession's lifetime -- diarization state must not leak across
sessions/patients.

Deliberately NOT retroactive: once an utterance is labeled, it stays labeled
(Blueprint Section 1 Principle 4: AI never overwrites the human-readable
transcript). A full offline/batch clustering pass (e.g. k-means over all
utterances at session end) would be more accurate but would mean re-labeling
utterances already shown to the user -- an online nearest-centroid approach
trades a little accuracy for never contradicting what's already on screen.

Capped at 2 speakers (Doctor/Patient, Blueprint Section 2.1) by design: a
third sufficiently-distinct voice is folded into whichever existing centroid
is nearest rather than spawning a third label, since this models a 2-party
consultation, not an open-ended multi-speaker meeting.
"""

from __future__ import annotations

import math

from app.diarization.provider import SpeakerEmbeddingProvider
from app.diarization.schemas import SpeakerAssignment

# Cosine distance above which a second voice is judged "new" rather than a
# noisy repeat of the first. Not tuned against a labeled gold set yet --
# qualitative starting point, flagged in docs/PROGRESS.md for revisit once
# real multi-speaker consultation audio is available.
NEW_SPEAKER_DISTANCE_THRESHOLD = 0.35

_SPEAKER_A = "speaker_a"
_SPEAKER_B = "speaker_b"


def _cosine_distance(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 1.0
    return 1.0 - (dot / (norm_a * norm_b))


class SpeakerDiarizer:
    def __init__(self, embedding_provider: SpeakerEmbeddingProvider) -> None:
        self._embedding_provider = embedding_provider
        self._centroids: dict[str, list[float]] = {}
        self._counts: dict[str, int] = {}

    def assign_speaker(self, pcm16_mono: bytes, sample_rate: int) -> SpeakerAssignment:
        embedding = self._embedding_provider.embed(pcm16_mono, sample_rate)

        if not self._centroids:
            self._seed_speaker(_SPEAKER_A, embedding)
            return SpeakerAssignment(speaker_label=_SPEAKER_A, confidence=1.0)

        distances = {label: _cosine_distance(embedding, centroid) for label, centroid in self._centroids.items()}
        nearest_label = min(distances, key=lambda label: distances[label])
        nearest_distance = distances[nearest_label]

        if len(self._centroids) < 2 and nearest_distance > NEW_SPEAKER_DISTANCE_THRESHOLD:
            new_label = _SPEAKER_B if _SPEAKER_A in self._centroids else _SPEAKER_A
            self._seed_speaker(new_label, embedding)
            return SpeakerAssignment(speaker_label=new_label, confidence=1.0)

        self._update_centroid(nearest_label, embedding)
        confidence = max(0.0, min(1.0, 1.0 - nearest_distance))
        return SpeakerAssignment(speaker_label=nearest_label, confidence=confidence)

    def _seed_speaker(self, label: str, embedding: list[float]) -> None:
        self._centroids[label] = embedding
        self._counts[label] = 1

    def _update_centroid(self, label: str, embedding: list[float]) -> None:
        count = self._counts[label]
        centroid = self._centroids[label]
        self._centroids[label] = [(c * count + e) / (count + 1) for c, e in zip(centroid, embedding)]
        self._counts[label] = count + 1
