"""Tests for experience duration parsing."""

import pytest

from app.utils.experience_parser import (
    calculate_total_experience,
    parse_duration,
    parse_experience_requirement,
)


class TestParseDuration:
    def test_date_range_full(self):
        assert parse_duration("2022-02 - 2024-06") == pytest.approx(2.33, abs=0.05)

    def test_date_range_years_only(self):
        assert parse_duration("2022 - 2024") == pytest.approx(2.0, abs=0.05)

    def test_date_range_present(self):
        result = parse_duration("2022-02 - Present")
        assert result > 3.0  # at least 3 years from 2022 to now

    def test_date_range_now(self):
        result = parse_duration("2024 - Now")
        assert result > 1.0

    def test_prose_years_months(self):
        assert parse_duration("2 years 4 months") == pytest.approx(2.33, abs=0.01)

    def test_prose_years_only(self):
        assert parse_duration("5 years") == 5.0

    def test_prose_months_only(self):
        assert parse_duration("18 months") == pytest.approx(1.5, abs=0.01)

    def test_shorthand_y(self):
        assert parse_duration("3y") == 3.0

    def test_shorthand_y_m(self):
        assert parse_duration("2y 6m") == pytest.approx(2.5, abs=0.01)

    def test_single_year(self):
        assert parse_duration("2020 - 2021") == 1.0

    def test_empty_string(self):
        assert parse_duration("") == 0.0

    def test_none(self):
        assert parse_duration(None) == 0.0  # type: ignore

    def test_decimal_years(self):
        assert parse_duration("1.5 years") == 1.5

    def test_date_range_ongoing_short(self):
        result = parse_duration("2025-01 - Current")
        assert result > 0.0


class TestCalculateTotalExperience:
    def test_multiple_entries(self):
        exp = [
            {"title": "SE", "company": "A", "duration": "2 years"},
            {"title": "SSE", "company": "B", "duration": "1 year 6 months"},
        ]
        assert calculate_total_experience(exp) == pytest.approx(3.5, abs=0.01)

    def test_empty_list(self):
        assert calculate_total_experience([]) == 0.0

    def test_ignores_missing_duration(self):
        exp = [
            {"title": "SE", "company": "A"},
            {"title": "SSE", "company": "B", "duration": "3 years"},
        ]
        assert calculate_total_experience(exp) == 3.0


class TestParseExperienceRequirement:
    def test_range_pattern(self):
        min_y, max_y = parse_experience_requirement("Looking for 3-5 years of experience")
        assert min_y == 3.0
        assert max_y == 5.0

    def test_plus_pattern(self):
        min_y, max_y = parse_experience_requirement("5+ years of Python experience required")
        assert min_y == 5.0
        assert max_y == float("inf")

    def test_at_least_pattern(self):
        min_y, max_y = parse_experience_requirement("At least 3 years experience in backend")
        assert min_y == 3.0
        assert max_y == float("inf")

    def test_minimum_pattern(self):
        min_y, max_y = parse_experience_requirement("Minimum 2 years of experience")
        assert min_y == 2.0
        assert max_y == float("inf")

    def test_exactish_pattern(self):
        min_y, max_y = parse_experience_requirement("5 years experience in DevOps")
        assert min_y == 4.0
        assert max_y == 6.0

    def test_no_requirement(self):
        min_y, max_y = parse_experience_requirement("We are looking for a great team player")
        assert min_y == 0.0
        assert max_y == float("inf")

    def test_none_text(self):
        min_y, max_y = parse_experience_requirement(None)
        assert min_y == 0.0
        assert max_y == float("inf")

    def test_range_with_to(self):
        min_y, max_y = parse_experience_requirement("3 to 5 years")
        assert min_y == 3.0
        assert max_y == 5.0
