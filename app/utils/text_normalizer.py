"""Normalize text for matching: locations, degrees, embedding-ready cleaning."""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Location normalization
# ---------------------------------------------------------------------------

# Canonical city names (handle common variants)
_CITY_ALIASES: dict[str, str] = {
    "bengaluru": "bangalore",
    "blr": "bangalore",
    "mumbai": "mumbai",
    "bombay": "mumbai",
    "delhi": "delhi",
    "new delhi": "delhi",
    "gurgaon": "gurugram",
    "gurugram": "gurugram",
    "hyderabad": "hyderabad",
    "hyd": "hyderabad",
    "pune": "pune",
    "chennai": "chennai",
    "madras": "chennai",
    "sf": "san francisco",
    "san fran": "san francisco",
    "nyc": "new york",
    "new york city": "new york",
    "la": "los angeles",
    "washington dc": "washington",
    "dc": "washington",
    "sfo": "san francisco",
    "mtv": "mountain view",
    "bay area": "san francisco",
}

# Country-level aliases
_COUNTRY_MAP: dict[str, str] = {
    "us": "united states",
    "usa": "united states",
    "uk": "united kingdom",
    "uae": "united arab emirates",
    "in": "india",
}

# Remote detection
_REMOTE_PATTERNS = re.compile(
    r"\b(remote|anywhere|work\s*from\s*home|wfh|distributed|virtual|global)\b",
    re.IGNORECASE,
)


def normalize_location(location: str | None) -> dict:
    """Normalize a location string into structured components.

    Returns a dict with: raw, city, state, country, is_remote
    """
    result: dict = {
        "raw": location,
        "city": None,
        "state": None,
        "country": None,
        "is_remote": False,
    }

    if not location:
        return result

    text = location.strip().lower()

    # Remote detection
    if _REMOTE_PATTERNS.search(text):
        result["is_remote"] = True
        return result

    # Split by comma
    parts = [p.strip() for p in text.split(",")]

    if len(parts) >= 1:
        city = parts[0]
        result["city"] = _CITY_ALIASES.get(city, city)

    if len(parts) >= 2:
        # Could be state or country
        second = parts[1]
        if len(second) == 2:  # state code
            result["state"] = second.upper()
        else:
            # Check country map
            result["country"] = _COUNTRY_MAP.get(second, second)

    if len(parts) >= 3:
        result["country"] = _COUNTRY_MAP.get(parts[2].strip(), parts[2].strip())

    return result


def location_match_score(
    candidate_locations: list[str | None],
    job_location: str | None,
    candidate_open_to_remote: bool = True,
) -> float:
    """Score a job location against candidate preferences.

    Returns 0-100 score.
    """
    if not job_location:
        return 50.0  # neutral

    job_norm = normalize_location(job_location)

    # Remote job scoring
    if job_norm["is_remote"]:
        return 100.0 if candidate_open_to_remote else 50.0

    if not any(candidate_locations):
        return 50.0

    best_score = 0.0
    for loc in candidate_locations:
        if not loc:
            continue
        cand_norm = normalize_location(loc)

        if job_norm["city"] and cand_norm["city"]:
            if job_norm["city"] == cand_norm["city"]:
                best_score = max(best_score, 100.0)
            elif job_norm.get("state") and cand_norm.get("state") and job_norm["state"] == cand_norm["state"]:
                best_score = max(best_score, 70.0)
            elif job_norm.get("country") and cand_norm.get("country") and job_norm["country"] == cand_norm["country"]:
                best_score = max(best_score, 50.0)

        if job_norm.get("state") and cand_norm.get("state") and job_norm["state"] == cand_norm["state"]:
            best_score = max(best_score, 70.0)

        if job_norm.get("country") and cand_norm.get("country") and job_norm["country"] == cand_norm["country"]:
            best_score = max(best_score, 50.0)

    return best_score if best_score > 0 else 30.0


# ---------------------------------------------------------------------------
# Degree / education normalization
# ---------------------------------------------------------------------------

_DEGREE_LEVELS: dict[str, int] = {
    "phd": 5,
    "doctorate": 5,
    "doctoral": 5,
    "ph.d": 5,
    "master": 4,
    "masters": 4,
    "m.s.": 4,
    "m.s": 4,
    "m.tech": 4,
    "m.e.": 4,
    "mba": 4,
    "m.a.": 4,
    "m.sc": 4,
    "postgraduate": 4,
    "bachelor": 3,
    "bachelors": 3,
    "b.tech": 3,
    "b.e.": 3,
    "b.s.": 3,
    "b.s": 3,
    "b.a.": 3,
    "b.sc": 3,
    "undergraduate": 3,
    "associate": 2,
    "diploma": 2,
    "certificate": 1,
    "high school": 0,
    "hs": 0,
}

_FIELD_ALIASES: dict[str, str] = {
    "cs": "computer science",
    "cse": "computer science",
    "it": "information technology",
    "ece": "electronics",
    "ee": "electrical engineering",
    "mech": "mechanical engineering",
    "ai": "artificial intelligence",
    "ml": "machine learning",
    "ds": "data science",
    "swe": "software engineering",
    "maths": "mathematics",
}


def normalize_education(degree: str) -> dict:
    """Parse a degree string into structured components.

    Returns: {level: int, level_name: str, field: str | None}
    """
    text = degree.lower().strip()
    level = -1
    level_name = "unknown"
    field = None

    # Detect degree level
    for keyword, lvl in sorted(_DEGREE_LEVELS.items(), key=lambda x: -len(x[0])):
        if keyword in text:
            level = lvl
            break

    if level == 5:
        level_name = "doctorate"
    elif level == 4:
        level_name = "master"
    elif level == 3:
        level_name = "bachelor"
    elif level == 2:
        level_name = "associate"
    elif level == 1:
        level_name = "certificate"
    elif level == 0:
        level_name = "high school"

    # Detect field
    for alias, canonical in sorted(_FIELD_ALIASES.items(), key=lambda x: -len(x[0])):
        if alias in text:
            field = canonical
            break

    if field is None:
        # Try to extract field name after "in "
        m = re.search(r"\bin\s+([\w\s]+)", text)
        if m:
            field = m.group(1).strip()

    return {"level": level, "level_name": level_name, "field": field}


def education_match_score(candidate_education: list[dict], job_description: str | None) -> float:
    """Score education match between candidate and job.

    Job education requirements are parsed heuristically from description.
    Returns 0-100.
    """
    if not job_description:
        return 50.0  # neutral

    if not candidate_education:
        return 30.0  # no education data from candidate

    job_desc_lower = job_description.lower()

    # Extract required education level from job description
    required_level = -1
    for keyword, lvl in sorted(_DEGREE_LEVELS.items(), key=lambda x: -len(x[0])):
        if keyword in job_desc_lower:
            required_level = max(required_level, lvl)

    # Get candidate's highest education level
    candidate_level = -1
    candidate_field = None
    for edu in candidate_education:
        degree = edu.get("degree", "") if isinstance(edu, dict) else getattr(edu, "degree", "")
        parsed = normalize_education(degree)
        candidate_level = max(candidate_level, parsed["level"])
        if parsed["field"]:
            candidate_field = parsed["field"]

    if required_level < 0:
        return 60.0  # job doesn't specify education requirement

    # Level scoring
    if candidate_level >= required_level:
        level_score = 100.0
    elif candidate_level == required_level - 1:
        level_score = 60.0  # one level below
    else:
        level_score = 20.0  # significantly below

    # Field bonus (up to 20 extra points)
    field_bonus = 0.0
    if candidate_field and candidate_field in job_desc_lower:
        field_bonus = 20.0

    return min(level_score + field_bonus, 100.0)


# ---------------------------------------------------------------------------
# Text cleaning for embeddings
# ---------------------------------------------------------------------------

_HTML_REMNANT = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"\s+")


def clean_for_embedding(text: str | None, max_chars: int = 2000) -> str:
    """Clean text for embedding generation: strip HTML, collapse whitespace, truncate."""
    if not text:
        return ""
    text = _HTML_REMNANT.sub(" ", text)
    text = _WHITESPACE.sub(" ", text)
    text = text.strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0]  # break at word boundary
    return text


def build_candidate_text(profile) -> str:
    """Build a combined text representation of a candidate profile for embedding."""
    parts = []

    if hasattr(profile, "summary") and profile.summary:
        parts.append(profile.summary)

    if hasattr(profile, "skills") and profile.skills:
        parts.append("Skills: " + ", ".join(profile.skills))

    if hasattr(profile, "experience") and profile.experience:
        titles = []
        for exp in profile.experience:
            title = exp.title if hasattr(exp, "title") else exp.get("title", "")
            desc = exp.description if hasattr(exp, "description") else exp.get("description", "")
            if desc:
                titles.append(f"{title}: {desc}")
            else:
                titles.append(title)
        parts.append("Experience: " + "; ".join(titles))

    return clean_for_embedding(" ".join(parts))
