"""Tests for skills matching logic."""

import pytest

from app.services.matching.structured.skills_matcher import (
    get_compatible_seniority_levels,
    match_skills,
)
from app.services.matching.taxonomy.aliases import normalize_skill_set, resolve_skill
from app.services.matching.taxonomy.hierarchy import (
    compute_hierarchical_overlap,
    get_children,
    get_parents,
)


class TestAliases:
    def test_resolve_py_to_python(self):
        assert resolve_skill("py") == "python"

    def test_resolve_js_to_javascript(self):
        assert resolve_skill("js") == "javascript"

    def test_resolve_k8s_to_kubernetes(self):
        assert resolve_skill("k8s") == "kubernetes"

    def test_resolve_unknown_passes_through(self):
        assert resolve_skill("some_obscure_skill") == "some_obscure_skill"

    def test_case_insensitive(self):
        assert resolve_skill("PyThOn") == "python"

    def test_normalize_skill_set(self):
        result = normalize_skill_set(["py", "js", "react", "some_unique"])
        assert result == {"python", "javascript", "react", "some_unique"}


class TestHierarchy:
    def test_get_children(self):
        children = get_children("frontend")
        assert "react" in children
        assert "angular" in children

    def test_get_parents(self):
        parents = get_parents("react")
        assert "frontend" in parents

    def test_hierarchical_overlap_parent_to_child(self):
        matched = compute_hierarchical_overlap({"frontend"}, {"react", "angular"})
        assert "frontend" in matched

    def test_hierarchical_overlap_child_to_parent(self):
        matched = compute_hierarchical_overlap({"react"}, {"frontend"})
        assert "react" in matched


class TestMatchSkills:
    def test_exact_match(self):
        # Job has one extra skill (docker) → not a perfect 100
        result = match_skills(["python", "fastapi", "aws"], ["python", "fastapi", "aws", "docker"])
        assert result["score"] == 85.0  # 0.6*0.75 + 0.4*1.0

    def test_perfect_match(self):
        result = match_skills(["python", "fastapi"], ["python", "fastapi"])
        assert result["score"] == 100.0

    def test_partial_match(self):
        result = match_skills(["python", "fastapi", "aws"], ["python", "docker"])
        assert 20 < result["score"] < 40  # only python overlaps

    def test_no_match(self):
        result = match_skills(["python", "fastapi"], ["java", "spring"])
        assert result["score"] == 0.0

    def test_with_aliases(self):
        result = match_skills(["py", "k8s"], ["python", "kubernetes"])
        assert result["score"] == 100.0

    def test_hierarchical_partial(self):
        result = match_skills(["frontend", "python"], ["react", "vue", "python"])
        assert result["score"] > 50.0  # "frontend" → matches react, vue

    def test_empty_job_skills(self):
        result = match_skills(["python", "aws"], None)
        assert result["score"] == 50.0  # neutral

    def test_empty_candidate_skills(self):
        result = match_skills([], ["python", "aws"])
        assert result["score"] == 0.0

    def test_matched_and_missing(self):
        result = match_skills(["python", "aws", "docker"], ["python", "java"])
        assert "python" in result["matched"]
        assert "aws" in result["missing"]
        assert "docker" in result["missing"]


class TestSeniorityLevels:
    def test_junior(self):
        levels = get_compatible_seniority_levels(1.0)
        assert "junior" in levels
        assert "staff" not in levels

    def test_mid(self):
        levels = get_compatible_seniority_levels(3.5)
        assert "mid" in levels
        assert "senior" in levels

    def test_senior(self):
        levels = get_compatible_seniority_levels(6.0)
        assert "senior" in levels
        assert "lead" in levels

    def test_staff(self):
        levels = get_compatible_seniority_levels(10.0)
        assert "staff" in levels
        assert "lead" in levels
        assert "junior" not in levels
