"""Matching engine orchestrator — two-pass pipeline: structured filter → semantic re-rank → score."""

from __future__ import annotations

import uuid

from sqlalchemy import select, text

from app.config import MatchingWeights, matching_config
from app.db import async_session
from app.models.candidate import CandidateProfile
from app.models.job_orm import Job
from app.models.match import JobMatch, ScoreBreakdown
from app.services.matching.scoring import ComponentScores, WeightedScorer
from app.services.matching.semantic.embedder import get_embedder
from app.services.matching.semantic.similarity import (
    batch_cosine_similarity,
    compute_description_similarity,
    compute_title_similarity,
)
from app.services.matching.structured.education_matcher import match_education
from app.services.matching.structured.experience_matcher import match_experience
from app.services.matching.structured.location_matcher import match_location
from app.services.matching.structured.skills_matcher import (
    get_compatible_seniority_levels,
    match_skills,
)
from app.utils.experience_parser import calculate_total_experience
from app.utils.text_normalizer import build_candidate_text, clean_for_embedding


class MatchingEngine:
    """Orchestrates the full matching pipeline."""

    def __init__(self, weights: MatchingWeights | None = None):
        self.scorer = WeightedScorer(weights)
        self.embedder = get_embedder()
        self._job_embeddings_cache: dict[uuid.UUID, dict] = {}

    async def match(
        self,
        profile: CandidateProfile,
        top_k: int = 20,
    ) -> list[JobMatch]:
        """Run the full matching pipeline and return ranked results."""
        # Compute total experience if not provided
        total_exp = profile.total_years_of_exp
        if total_exp == 0.0 and profile.experience:
            total_exp = calculate_total_experience(
                [e.model_dump() for e in profile.experience]
            )

        # Pass 1: Structured SQL filter
        jobs = await self._structured_filter(profile, total_exp)
        if not jobs:
            return []

        # Pass 2: Semantic embeddings for filtered subset
        candidate_embedding = await self._embed_candidate(profile, total_exp)

        # Build text for each job: title for title-sim, description for desc-sim
        job_texts = []
        for job in jobs:
            job_texts.append({
                "title": clean_for_embedding(job.title, 256),
                "description": clean_for_embedding(job.description, 1500),
            })

        # Batch encode job titles and descriptions
        title_embs = await self.embedder.encode([jt["title"] for jt in job_texts])
        desc_embs = await self.embedder.encode([
            jt["description"] if jt["description"] else jt["title"]
            for jt in job_texts
        ])

        # Pass 3: Full scoring
        scored: list[JobMatch] = []
        for i, job in enumerate(jobs):
            # Structured scores
            skills_result = match_skills(profile.skills, job.skills)
            exp_result = match_experience(total_exp, job.description, job.seniority_level)
            loc_result = match_location(
                profile.preferred_location,
                profile.current_location,
                job.location,
            )
            edu_result = match_education(
                [e.model_dump() for e in profile.education],
                job.description,
            )

            # Semantic scores
            title_sim = compute_title_similarity(candidate_embedding, title_embs[i])
            desc_sim = compute_description_similarity(candidate_embedding, desc_embs[i])

            scores = ComponentScores(
                skills_score=skills_result["score"],
                experience_score=exp_result["score"],
                title_similarity=title_sim,
                description_similarity=desc_sim,
                education_score=edu_result["score"],
                location_score=loc_result["score"],
            )

            final_score = self.scorer.compute_final(scores)

            # Build reason
            reason = _build_reason(scores, skills_result, exp_result)

            scored.append(JobMatch(
                job_id=job.id,
                title=job.title,
                company=job.company or "Unknown",
                location=job.location,
                description=_truncate(job.description, 500),
                url=job.url,
                final_score=final_score,
                score_breakdown=ScoreBreakdown(**scores.to_dict()),
                matched_skills=skills_result["matched"],
                missing_skills=skills_result["missing"],
                reason=reason,
            ))

        # Sort by final_score DESC
        scored.sort(key=lambda m: m.final_score, reverse=True)
        return scored[:top_k]

    async def _structured_filter(
        self,
        profile: CandidateProfile,
        total_exp: float,
    ) -> list[Job]:
        """Pass 1: Filter jobs from DB using structured criteria."""
        async with async_session() as session:
            conditions = [Job.is_active == True]

            # Location filter: prefer preferred + current, but don't exclude others
            # We use ILIKE for fuzzy matching; exact matching happens in scoring

            # Seniority filter: compatible levels based on experience
            compatible_levels = get_compatible_seniority_levels(total_exp)
            if compatible_levels:
                conditions.append(
                    Job.seniority_level.in_(compatible_levels) |
                    (Job.seniority_level == None)
                )

            query = (
                select(Job)
                .where(*conditions)
                .order_by(Job.posted_at.desc())
                .limit(matching_config.structured_filter_limit)
            )

            result = await session.execute(query)
            jobs = result.scalars().all()
            return list(jobs)

    async def _embed_candidate(
        self,
        profile: CandidateProfile,
        total_exp: float,
    ):
        """Build and embed the candidate profile."""
        # Build a rich text representation for the candidate
        text = build_candidate_text(profile)
        if total_exp > 0:
            text += f" | {total_exp} years of experience"
        if profile.preferred_location:
            text += f" | Seeking roles in {profile.preferred_location}"

        emb = await self.embedder.encode([text])
        return emb[0] if len(emb) > 0 else None


def _build_reason(
    scores: ComponentScores,
    skills_result: dict,
    exp_result: dict,
) -> str:
    """Generate a human-readable match explanation."""
    parts = []

    if scores.skills_score >= 80:
        parts.append(f"Strong skill match ({skills_result['matched'][:5]})")
    elif scores.skills_score >= 50:
        parts.append("Moderate skill overlap")
    elif scores.skills_score > 0:
        parts.append(f"Missing key skills: {skills_result['missing'][:3]}")

    if scores.experience_score >= 90:
        parts.append("experience level fits perfectly")
    elif scores.experience_score >= 70:
        parts.append("experience level is compatible")
    elif scores.experience_score < 50:
        parts.append("experience level may not match")

    if scores.title_similarity >= 75:
        parts.append("high title relevance")
    if scores.description_similarity >= 75:
        parts.append("strong profile alignment")

    if not parts:
        return "Limited match across all dimensions"

    return ". ".join(parts) + "."


def _truncate(text: str | None, max_chars: int) -> str | None:
    """Truncate text at word boundary."""
    if not text:
        return text
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."
