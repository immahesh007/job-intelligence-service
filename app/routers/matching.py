"""Job-candidate matching API endpoints."""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, HTTPException, Query

from app.config import matching_config
from app.models.candidate import CandidateProfile
from app.models.job_orm import Job
from app.models.match import (
    JobMatch,
    MatchRequest,
    MatchResponse,
    ScoreBreakdown,
)
from app.services.matching.engine import MatchingEngine
from app.services.matching.scoring import ComponentScores

router = APIRouter(prefix="/api", tags=["matching"])


@router.post("/matching", response_model=MatchResponse)
async def match_jobs(
    request: MatchRequest,
    top_k: int = Query(20, ge=1, le=100, description="Max results to return"),
    min_score: float = Query(0.0, ge=0, le=100, description="Minimum final score threshold"),
):
    """Match a candidate profile against all active jobs and return ranked results.

    The matching engine combines:
    - **Structured matching**: skills overlap (Jaccard + hierarchy), experience range,
      location proximity, education level
    - **Semantic matching**: cosine similarity on title and description embeddings
    - **Weighted scoring**: configurable weights combining all signals into final_score

    Results are sorted by `final_score` descending.
    """
    engine = MatchingEngine(weights=request.weights)

    try:
        matches = await engine.match(request.candidate, top_k=top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")

    # Apply min_score filter
    matches = [m for m in matches if m.final_score >= min_score]

    return MatchResponse(
        total_matches=len(matches),
        matches=matches,
        matching_config={
            "weights": engine.scorer.to_dict(),
            "embedder": engine.embedder.name,
            "top_k_requested": top_k,
            "min_score": min_score,
        },
    )


@router.post("/matching/explain")
async def explain_match(
    candidate: CandidateProfile,
    job_id: uuid.UUID = Query(..., description="Job ID to explain the match for"),
):
    """Debug endpoint: return detailed scoring diagnostics for a single job match.

    Returns every component score, raw embeddings, and intermediate calculations
    so you can tune weights and understand matching behavior.
    """
    from app.db import async_session
    from app.services.matching.semantic.embedder import get_embedder
    from app.services.matching.semantic.similarity import (
        compute_description_similarity,
        compute_title_similarity,
    )
    from app.services.matching.structured.education_matcher import match_education
    from app.services.matching.structured.experience_matcher import match_experience
    from app.services.matching.structured.location_matcher import match_location
    from app.services.matching.structured.skills_matcher import match_skills
    from app.utils.experience_parser import calculate_total_experience
    from app.utils.text_normalizer import build_candidate_text, clean_for_embedding

    # Load the job
    async with async_session() as session:
        job = await session.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    total_exp = candidate.total_years_of_exp
    if total_exp == 0.0 and candidate.experience:
        total_exp = calculate_total_experience(
            [e.model_dump() for e in candidate.experience]
        )

    # Structured scores
    skills_result = match_skills(candidate.skills, job.skills)
    exp_result = match_experience(total_exp, job.description, job.seniority_level)
    loc_result = match_location(
        candidate.preferred_location,
        candidate.current_location,
        job.location,
    )
    edu_result = match_education(
        [e.model_dump() for e in candidate.education],
        job.description,
    )

    # Semantic scores
    embedder = get_embedder()
    candidate_text = build_candidate_text(candidate)
    if total_exp > 0:
        candidate_text += f" | {total_exp} years of experience"

    cand_emb = await embedder.encode([candidate_text])
    job_title_emb = await embedder.encode([clean_for_embedding(job.title, 256)])
    job_desc_emb = await embedder.encode([
        clean_for_embedding(job.description, 1500) if job.description else job.title
    ])

    title_sim = compute_title_similarity(cand_emb[0], job_title_emb[0])
    desc_sim = compute_description_similarity(cand_emb[0], job_desc_emb[0])

    scores = ComponentScores(
        skills_score=skills_result["score"],
        experience_score=exp_result["score"],
        title_similarity=title_sim,
        description_similarity=desc_sim,
        education_score=edu_result["score"],
        location_score=loc_result["score"],
    )

    from app.services.matching.scoring import WeightedScorer
    scorer = WeightedScorer(matching_config.weights)
    final_score = scorer.compute_final(scores)

    return {
        "job_id": str(job.id),
        "job_title": job.title,
        "job_company": job.company,
        "job_location": job.location,
        "candidate_summary": {
            "total_years_exp": total_exp,
            "skills": candidate.skills,
            "preferred_location": candidate.preferred_location,
            "current_location": candidate.current_location,
        },
        "final_score": final_score,
        "score_breakdown": scores.to_dict(),
        "weights": scorer.to_dict(),
        "structured_details": {
            "skills": skills_result,
            "experience": exp_result,
            "location": loc_result,
            "education": edu_result,
        },
        "semantic_details": {
            "title_similarity_raw": title_sim,
            "description_similarity_raw": desc_sim,
            "candidate_text_embedded": candidate_text[:300],
            "job_title_embedded": clean_for_embedding(job.title, 256),
            "job_description_embedded": clean_for_embedding(job.description, 300),
        },
        "embedder": embedder.name,
    }
