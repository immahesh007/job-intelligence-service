"""Skills matching — Jaccard + overlap ratio with alias and hierarchy support."""

from __future__ import annotations

from app.services.matching.taxonomy.aliases import normalize_skill_set
from app.services.matching.taxonomy.hierarchy import compute_hierarchical_overlap


def match_skills(candidate_skills: list[str], job_skills: list[str] | None) -> dict:
    """Score skill overlap between candidate and job.

    Returns: {score: float 0-100, matched: list[str], missing: list[str], coverage: float}
    """
    if not candidate_skills:
        return {"score": 0.0, "matched": [], "missing": [], "coverage": 0.0}

    cand_set = normalize_skill_set(candidate_skills)
    job_set = normalize_skill_set(job_skills) if job_skills else set()

    if not job_set:
        return {"score": 50.0, "matched": list(cand_set), "missing": [], "coverage": 0.5}

    # Direct intersection
    direct_matches = cand_set & job_set

    # Hierarchical matches (parent/child relationships)
    hierarchical_matches = compute_hierarchical_overlap(cand_set, job_set)

    all_matched = direct_matches | hierarchical_matches
    missing = cand_set - job_set  # candidate has but job doesn't mention

    # Jaccard similarity: |intersection| / |union|
    union = cand_set | job_set
    jaccard = len(all_matched) / len(union) if union else 0.0

    # Overlap ratio: what % of candidate skills are found in the job
    overlap_ratio = len(all_matched) / len(cand_set) if cand_set else 0.0

    # Combined score: 60% Jaccard + 40% overlap (scales 0-100)
    score = (0.6 * jaccard + 0.4 * overlap_ratio) * 100.0

    return {
        "score": round(score, 1),
        "matched": sorted(all_matched),
        "missing": sorted(missing - all_matched),
        "coverage": round(overlap_ratio, 2),
    }


def get_compatible_seniority_levels(candidate_years: float) -> list[str]:
    """Return seniority levels compatible with the candidate's experience."""
    if candidate_years >= 8:
        return ["senior", "lead", "staff", "mid"]
    elif candidate_years >= 5:
        return ["senior", "mid", "lead"]
    elif candidate_years >= 3:
        return ["mid", "senior", "junior"]
    elif candidate_years >= 1:
        return ["junior", "mid"]
    else:
        return ["junior", "mid", "senior", "lead", "staff"]  # return all for fresh grads
