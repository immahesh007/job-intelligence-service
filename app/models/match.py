from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.config import MatchingWeights
from app.models.candidate import CandidateProfile


class ScoreBreakdown(BaseModel):
    """Per-component scores (0-100)."""

    skills_score: float = Field(0.0, ge=0, le=100)
    experience_score: float = Field(0.0, ge=0, le=100)
    title_similarity: float = Field(0.0, ge=0, le=100)
    description_similarity: float = Field(0.0, ge=0, le=100)
    education_score: float = Field(0.0, ge=0, le=100)
    location_score: float = Field(0.0, ge=0, le=100)


class JobMatch(BaseModel):
    """A single matched job result."""

    job_id: uuid.UUID
    title: str
    company: str
    location: str | None
    description: str | None = Field(None, description="First 500 chars of job description")
    url: str | None
    final_score: float = Field(..., ge=0, le=100)
    score_breakdown: ScoreBreakdown
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    reason: str = Field("", description="Human-readable match explanation")


class MatchRequest(BaseModel):
    """Request payload for the matching API."""

    candidate: CandidateProfile
    weights: MatchingWeights | None = Field(None, description="Optional custom scoring weights")


class MatchResponse(BaseModel):
    """Response from the matching API."""

    total_matches: int
    matches: list[JobMatch]
    matching_config: dict = Field(default_factory=dict)
