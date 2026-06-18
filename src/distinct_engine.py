"""Distinctness checks for Scene DNA creative directions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


SIMILARITY_WEIGHTS = {
    "architecture": 0.25,
    "spatial_layout": 0.20,
    "lighting": 0.20,
    "materials": 0.15,
    "props_styling": 0.05,
    "camera": 0.10,
    "color_mood": 0.05,
}

SIMILARITY_THRESHOLD = 0.70


def calculate_similarity(
    first: Mapping[str, object],
    second: Mapping[str, object],
    weights: Mapping[str, float] = SIMILARITY_WEIGHTS,
) -> float:
    """Calculate weighted layer similarity between two creative directions."""

    score = 0.0
    for field, weight in weights.items():
        if _normalize(first.get(field)) == _normalize(second.get(field)):
            score += weight
    return round(score, 4)


def is_distinct(
    candidate: Mapping[str, object],
    accepted: Sequence[Mapping[str, object]],
    threshold: float = SIMILARITY_THRESHOLD,
) -> bool:
    """Return True when candidate is not too similar to accepted directions."""

    return all(calculate_similarity(candidate, existing) <= threshold for existing in accepted)


def highest_similarity(
    candidate: Mapping[str, object],
    accepted: Sequence[Mapping[str, object]],
) -> float:
    """Return the highest similarity score against accepted directions."""

    if not accepted:
        return 0.0
    return max(calculate_similarity(candidate, existing) for existing in accepted)


def _normalize(value: object) -> str:
    return str(value or "").strip().lower()
