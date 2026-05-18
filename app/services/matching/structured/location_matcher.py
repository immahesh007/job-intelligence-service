"""Location matching — city/state/country comparison with remote support."""

from __future__ import annotations

from app.utils.text_normalizer import location_match_score


def match_location(
    preferred_location: str | None,
    current_location: str | None,
    job_location: str | None,
    open_to_remote: bool = True,
) -> dict:
    """Score location match between candidate preferences and job location.

    Returns: {score: float 0-100, matched_city: str | None, is_remote: bool}
    """
    locations = [loc for loc in (preferred_location, current_location) if loc]

    score = location_match_score(locations, job_location, open_to_remote)

    return {
        "score": round(score, 1),
        "matched_city": job_location,
        "is_remote": job_location and "remote" in job_location.lower() if job_location else False,
    }
