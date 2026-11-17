from decimal import Decimal

from django.test import SimpleTestCase

from dashboard.score_distribution import build_score_summary


class ScoreDistributionTests(SimpleTestCase):
    def test_bands_include_decimals_and_both_score_boundaries(self):
        summary = build_score_summary([0, Decimal("1.5"), Decimal("4.99"), 5, -1, 11])

        self.assertEqual(summary["sample_size"], 4)
        self.assertEqual([band["count"] for band in summary["bands"]], [1, 1, 0, 0, 2])
        self.assertEqual(summary["suggested_score"], None)

    def test_odd_sample_rounds_median_and_counts_scores_at_or_above(self):
        summary = build_score_summary([0, Decimal("2.2"), Decimal("4.4"), Decimal("4.6"), 5])

        self.assertEqual(summary["suggested_score"], Decimal("4.5"))
        self.assertEqual(summary["suggested_count"], 2)
        self.assertFalse(summary["suggestion_below_profile"])

    def test_even_sample_rounds_half_up(self):
        summary = build_score_summary([0, Decimal("2.5"), Decimal("3.5"), 4, Decimal("4.5"), 5])

        self.assertEqual(summary["suggested_score"], Decimal("4"))
        self.assertEqual(summary["suggested_count"], 3)

    def test_recommendation_below_profile_minimum_is_flagged(self):
        summary = build_score_summary([3, Decimal("3.5"), Decimal("3.5"), 4, Decimal("4.5")], minimum_score=4)

        self.assertEqual(summary["suggested_score"], Decimal("3.5"))
        self.assertTrue(summary["suggestion_below_profile"])

    def test_insufficient_sample_has_no_recommendation(self):
        summary = build_score_summary([1, Decimal("2.5"), 5])

        self.assertEqual(summary["sample_size"], 3)
        self.assertIsNone(summary["suggested_score"])
        self.assertEqual(summary["suggested_count"], 0)

