"""Experience matching — compare candidate years against job requirements."""

from __future__ import annotations

from app.utils.experience_parser import (
    SENIORITY_EXP_RANGE,
    parse_experience_requirement,
)


def match_experience(
    candidate_years: float,
    job_description: str | None = None,
    job_seniority: str | None = None,
) -> dict:
    """Score experience match between candidate and job.

    Returns: {score: float 0-100, candidate_years: float, required_min: float, required_max: float}
    """
    # Determine job's expected experience range
    req_min, req_max = parse_experience_requirement(job_description)

    # Fallback to seniority inference if description didn't yield a requirement
    if req_min == 0.0 and req_max == float("inf") and job_seniority:
        req_min, req_max = SENIORITY_EXP_RANGE.get(job_seniority.lower(), (0.0, float("inf")))

    # No requirement found at all — neutral score
    if req_min == 0.0 and req_max == float("inf"):
        return {
            "score": 60.0,
            "candidate_years": candidate_years,
            "required_min": None,
            "required_max": None,
            "fit": "unknown",
        }

    # Scoring logic
    if req_min <= candidate_years <= req_max:
        score = 100.0
        fit = "exact"
    elif candidate_years < req_min:
        gap = req_min - candidate_years
        if gap <= 1.0:
            score = 70.0
            fit = "slightly_below"
        elif gap <= 2.0:
            score = 50.0
            fit = "below"
        else:
            score = max(20.0, 30.0 - (gap - 2.0) * 10.0)
            fit = "significantly_below"
    else:  # candidate_years > req_max
        score = 80.0
        fit = "overqualified"

    return {
        "score": round(score, 1),
        "candidate_years": candidate_years,
        "required_min": req_min if req_min > 0 else None,
        "required_max": req_max if req_max != float("inf") else None,
        "fit": fit,
    }
