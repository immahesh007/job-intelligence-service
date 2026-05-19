"""Tests for weighted scoring logic."""

import pytest

from app.config import MatchingWeights
from app.services.matching.scoring import ComponentScores, WeightedScorer


class TestMatchingWeights:
    def test_default_weights_sum_to_one(self):
        w = MatchingWeights()
        total = w.skills + w.experience + w.title_similarity + w.description_similarity + w.education + w.location
        assert abs(total - 1.0) < 0.01

    def test_invalid_weights_raise(self):
        with pytest.raises(ValueError):
            MatchingWeights(skills=1.0)  # sums > 1

    def test_custom_weights(self):
        w = MatchingWeights(skills=0.5, experience=0.2, title_similarity=0.05,
                            description_similarity=0.15, education=0.05, location=0.05)
        total = w.skills + w.experience + w.title_similarity + w.description_similarity + w.education + w.location
        assert abs(total - 1.0) < 0.01


class TestWeightedScorer:
    def test_perfect_scores(self):
        scorer = WeightedScorer()
        scores = ComponentScores(
            skills_score=100, experience_score=100,
            title_similarity=100, description_similarity=100,
            education_score=100, location_score=100,
        )
        assert scorer.compute_final(scores) == 100.0

    def test_zero_scores(self):
        scorer = WeightedScorer()
        scores = ComponentScores()
        assert scorer.compute_final(scores) == 0.0

    def test_mixed_scores(self):
        scorer = WeightedScorer()
        scores = ComponentScores(
            skills_score=80, experience_score=70,
            title_similarity=60, description_similarity=90,
            education_score=50, location_score=100,
        )
        final = scorer.compute_final(scores)
        # 0.35*80 + 0.20*70 + 0.15*60 + 0.20*90 + 0.05*50 + 0.05*100
        expected = 28 + 14 + 9 + 18 + 2.5 + 5
        assert final == pytest.approx(expected, abs=0.1)

    def test_custom_weights(self):
        w = MatchingWeights(skills=0.5, experience=0.1, title_similarity=0.1,
                            description_similarity=0.2, education=0.05, location=0.05)
        scorer = WeightedScorer(w)
        scores = ComponentScores(
            skills_score=80, experience_score=70,
            title_similarity=60, description_similarity=90,
            education_score=50, location_score=100,
        )
        final = scorer.compute_final(scores)
        expected = 0.5*80 + 0.1*70 + 0.1*60 + 0.2*90 + 0.05*50 + 0.05*100
        assert final == pytest.approx(expected, abs=0.1)

    def test_sort_order_descending(self):
        """Verify scores sort correctly in descending order."""
        scorer = WeightedScorer()
        results = []
        for s in [90, 50, 75, 100, 30]:
            scores = ComponentScores(skills_score=s)
            results.append(scorer.compute_final(scores))

        results.sort(reverse=True)
        assert results[0] > results[1] > results[2] > results[3] > results[4]
