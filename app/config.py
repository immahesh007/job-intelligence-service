import os
from dataclasses import dataclass, field
from pathlib import Path

from app.models.job import ATSProvider

COMPANIES_DIR = Path(__file__).resolve().parent.parent / "companies"

PROVIDER_FILES = {
    ATSProvider.GREENHOUSE: COMPANIES_DIR / "greenhouse.txt",
    ATSProvider.LEVER: COMPANIES_DIR / "lever.txt",
    ATSProvider.ASHBY: COMPANIES_DIR / "ashby.txt",
}


def load_companies(provider: ATSProvider) -> list[str]:
    """Return company slugs for a provider, one per line. Blank lines and #-comments are skipped."""
    path = PROVIDER_FILES[provider]
    if not path.exists():
        return []
    slugs: list[str] = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            slugs.append(stripped)
    return slugs


# ---------------------------------------------------------------------------
# Matching configuration
# ---------------------------------------------------------------------------


@dataclass
class MatchingWeights:
    """Configurable weights for the hybrid matching scorer. All values should sum to 1.0."""

    skills: float = 0.35
    experience: float = 0.20
    title_similarity: float = 0.15
    description_similarity: float = 0.20
    education: float = 0.05
    location: float = 0.05

    def __post_init__(self):
        total = (
            self.skills
            + self.experience
            + self.title_similarity
            + self.description_similarity
            + self.education
            + self.location
        )
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"MatchingWeights must sum to 1.0, got {total}")


@dataclass
class MatchingConfig:
    """Global configuration for the matching engine."""

    # Embedding provider: "sentence-transformers" (local) or "openai" (cloud)
    embedding_provider: str = field(
        default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "sentence-transformers")
    )
    # Model name for the selected provider
    embedding_model: str = field(
        default_factory=lambda: os.getenv(
            "EMBEDDING_MODEL", "all-MiniLM-L6-v2"
        )
    )
    # Max jobs to pass through to semantic scoring (limits embedding API calls)
    semantic_candidate_limit: int = 200
    # Max jobs returned by the structured SQL filter
    structured_filter_limit: int = 300
    # Default number of results to return
    default_top_k: int = 20
    # Default scoring weights
    weights: MatchingWeights = field(default_factory=MatchingWeights)


matching_config = MatchingConfig()
