"""Education matching — degree level + field of study comparison."""

from __future__ import annotations

from app.utils.text_normalizer import education_match_score


def match_education(
    candidate_education: list[dict],
    job_description: str | None = None,
) -> dict:
    """Score education match between candidate and job.

    Returns: {score: float 0-100, candidate_level: str, required_level: str | None}
    """
    score = education_match_score(candidate_education, job_description)

    from app.utils.text_normalizer import normalize_education

    best_level = "unknown"
    for edu in candidate_education:
        degree = edu.get("degree", "") if isinstance(edu, dict) else getattr(edu, "degree", "")
        parsed = normalize_education(degree)
        if parsed["level"] > 0:
            best_level = parsed["level_name"]

    return {
        "score": round(score, 1),
        "candidate_level": best_level,
    }
