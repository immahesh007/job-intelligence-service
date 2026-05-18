"""Weighted scoring system — combines structured and semantic scores into final rank."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.config import MatchingWeights


@dataclass
class ComponentScores:
    """Container for all component scores before weighting."""
    skills_score: float = 0.0
    experience_score: float = 0.0
    title_similarity: float = 0.0
    description_similarity: float = 0.0
    education_score: float = 0.0
    location_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "skills_score": self.skills_score,
            "experience_score": self.experience_score,
            "title_similarity": self.title_similarity,
            "description_similarity": self.description_similarity,
            "education_score": self.education_score,
            "location_score": self.location_score,
        }


class WeightedScorer:
    """Apply configurable weights to component scores and compute final score."""

    def __init__(self, weights: MatchingWeights | None = None):
        self.weights = weights or MatchingWeights()

    def compute_final(self, scores: ComponentScores) -> float:
        """Compute weighted final score (0-100)."""
        final = (
            self.weights.skills * scores.skills_score
            + self.weights.experience * scores.experience_score
            + self.weights.title_similarity * scores.title_similarity
            + self.weights.description_similarity * scores.description_similarity
            + self.weights.education * scores.education_score
            + self.weights.location * scores.location_score
        )
        return round(final, 1)

    def to_dict(self) -> dict:
        return {
            "skills": self.weights.skills,
            "experience": self.weights.experience,
            "title_similarity": self.weights.title_similarity,
            "description_similarity": self.weights.description_similarity,
            "education": self.weights.education,
            "location": self.weights.location,
        }
