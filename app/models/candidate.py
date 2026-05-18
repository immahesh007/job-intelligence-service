from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Education(BaseModel):
    degree: str = Field(..., description="Degree name, e.g. 'B.Tech Computer Science'")
    field: Optional[str] = Field(None, description="Field of study, e.g. 'Computer Science'")


class Experience(BaseModel):
    title: str = Field(..., description="Job title, e.g. 'Software Engineer II'")
    company: str = Field(..., description="Company name")
    duration: str = Field(
        ...,
        description="Duration string: 'YYYY-MM - YYYY-MM', 'N years M months', or 'YYYY - Present'",
    )
    description: Optional[str] = Field(None, description="Role description for semantic matching")


class CandidateProfile(BaseModel):
    """Candidate profile submitted for job matching."""

    summary: Optional[str] = Field(None, description="Brief professional summary")
    skills: list[str] = Field(..., min_length=1, description="Candidate skills (mixed technical + soft)")
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    total_years_of_exp: float = Field(
        default=0.0,
        ge=0.0,
        description="Total years of experience. If 0, auto-calculated from experience durations.",
    )
    preferred_location: Optional[str] = Field(None, description="Preferred job location")
    current_location: Optional[str] = Field(None, description="Current location")

    @model_validator(mode="after")
    def validate_at_least_one_signal(self):
        if not self.skills and not self.experience and not self.summary:
            raise ValueError("Provide at least one of: skills, experience, or summary")
        return self
