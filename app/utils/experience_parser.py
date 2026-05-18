"""Parse experience duration strings from candidate profiles into total years (float)."""

from __future__ import annotations

import re
from datetime import date, datetime

# Matches "YYYY-MM - YYYY-MM", "YYYY-MM - Present", "YYYY - YYYY", "YYYY - Present"
_DATE_RANGE = re.compile(
    r"(\d{4})(?:-(\d{1,2}))?\s*[-–—to]+\s*(\d{4}|present|now|current)(?:-(\d{1,2}))?",
    re.IGNORECASE,
)

# Matches prose: "N years M months", "N yrs M mos", "Ny Mm", "N.Y years"
_YEARS_MONTHS = re.compile(r"(\d+\.?\d*)\s*(?:years?|yrs?|y)\s*(?:and\s*)?(\d+\.?\d*)?\s*(?:months?|mos?|m)?", re.IGNORECASE)

# Matches just months: "N months"
_MONTHS_ONLY = re.compile(r"(\d+)\s*(?:months?|mos?)\b", re.IGNORECASE)

# Matches just years: "N years", "N yrs", "Ny"
_YEARS_ONLY = re.compile(r"(\d+\.?\d*)\s*(?:years?|yrs?|y)\b", re.IGNORECASE)


def parse_duration(duration_str: str) -> float:
    """Parse a single duration string and return years as a float.

    Supports:
      - Date ranges: "2022-02 - 2024-06", "2022 - Present", "2022 - 2024"
      - Prose: "2 years 4 months", "3 yrs", "1.5 years", "18 months"
      - Shorthand: "2y 4m", "2y", "6m"
    """
    if not duration_str or not duration_str.strip():
        return 0.0

    text = duration_str.strip()

    # 1. Try date range first
    m = _DATE_RANGE.fullmatch(text)
    if m:
        start_year = int(m.group(1))
        start_month = int(m.group(2)) if m.group(2) else 1
        end_str = m.group(3).lower()
        end_month = int(m.group(4)) if m.group(4) else 1

        if end_str in ("present", "now", "current"):
            end_date = date.today()
        else:
            end_date = date(int(end_str), end_month, 1)

        start_date = date(start_year, start_month, 1)
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        return max(round(months / 12.0, 2), 0.02)  # floor at ~1 week

    # 2. Try "N years M months" pattern
    m = _YEARS_MONTHS.search(text)
    if m:
        years = float(m.group(1)) if m.group(1) else 0.0
        months = float(m.group(2)) if m.group(2) else 0.0
        return round(years + months / 12.0, 2)

    # 3. Try months only
    m = _MONTHS_ONLY.search(text)
    if m:
        months = float(m.group(1))
        return round(months / 12.0, 2)

    # 4. Try years only
    m = _YEARS_ONLY.search(text)
    if m:
        return round(float(m.group(1)), 2)

    return 0.0


def calculate_total_experience(experience: list[dict] | list) -> float:
    """Calculate total years of experience from a list of experience entries.

    Each entry should have a 'duration' key with a parsable string.
    Overlapping periods are not deduplicated (candidate self-reports).
    """
    total = 0.0
    for exp in experience:
        dur = exp.get("duration", "") if isinstance(exp, dict) else getattr(exp, "duration", "")
        total += parse_duration(dur)
    return round(total, 2)


def parse_experience_requirement(text: str | None) -> tuple[float, float]:
    """Extract min/max years of experience from a job description.

    Returns (min_years, max_years). max_years may be float('inf') for "X+ years".
    Returns (0.0, float('inf')) if nothing found (no requirement).
    """
    if not text:
        return 0.0, float("inf")

    # "X-Y years", "X to Y years"
    range_pat = re.compile(r"(\d+\.?\d*)\s*[-–—to]+\s*(\d+\.?\d*)\s*(?:\+)?\s*years?", re.IGNORECASE)
    m = range_pat.search(text)
    if m:
        return float(m.group(1)), float(m.group(2))

    # "X+ years", "at least X years", "minimum X years", "min X years"
    min_pat = re.compile(
        r"(?:at\s*least|minimum|min|atleast)\s*(\d+\.?\d*)\s*(?:\+)?\s*years?|"
        r"(\d+\.?\d*)\+\s*years?",
        re.IGNORECASE,
    )
    m = min_pat.search(text)
    if m:
        val = float(m.group(1) or m.group(2))
        return val, float("inf")

    # "X years experience", "X years of experience" → treat as exact-ish
    exact_pat = re.compile(r"(\d+\.?\d*)\s*years?\s*(?:of\s*)?experience", re.IGNORECASE)
    m = exact_pat.search(text)
    if m:
        val = float(m.group(1))
        return max(0, val - 1), val + 1  # fuzzy range

    return 0.0, float("inf")


# Seniority → experience range inference
SENIORITY_EXP_RANGE: dict[str, tuple[float, float]] = {
    "junior": (0.0, 2.0),
    "mid": (2.0, 5.0),
    "senior": (5.0, 8.0),
    "lead": (8.0, 12.0),
    "staff": (8.0, float("inf")),
}
