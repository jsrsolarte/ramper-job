from decimal import Decimal
from unittest import TestCase

from matching.score_scale import (calculate_star_total, historical_profile_minimum,
                                  historical_score_to_stars, meets_captured_legacy_threshold, rounded_star_score)


class ScoreScaleTests(TestCase):
    def test_final_score_clamps_and_rounds_ties_up(self):
        for value, expected in [('-1', '0'), ('0.24', '0'), ('0.25', '0.5'),
                                ('3.24', '3'), ('3.25', '3.5'), ('4.75', '5'), ('6', '5')]:
            with self.subTest(value=value):
                self.assertEqual(rounded_star_score(value), Decimal(expected))

    def test_historical_score_and_profile_minimum_use_distinct_rules(self):
        self.assertEqual(historical_score_to_stars('6.5'), Decimal('3.5'))
        self.assertEqual(historical_score_to_stars('10'), Decimal('5'))
        self.assertEqual(historical_profile_minimum(5), 3)
        self.assertEqual(historical_profile_minimum(0), 0)
        self.assertEqual(historical_profile_minimum(10), 5)

    def test_sum_and_deductions_are_applied_before_final_rounding(self):
        self.assertEqual(calculate_star_total(['2', '0.75', '0.5', '0.5', '0.5'], ['1']), Decimal('3.5'))
        self.assertEqual(calculate_star_total(['0.2', '0.2'], ['1']), Decimal('0'))
        self.assertEqual(calculate_star_total(['2', '1', '1', '0.5', '0.5'], []), Decimal('5'))
        with self.assertRaises(ValueError):
            calculate_star_total(['-0.5'], [])

    def test_pending_legacy_threshold_compares_before_rounding(self):
        # 5.9/10 rounds to 3 stars, but is still below the captured 6/10 threshold.
        self.assertEqual(historical_score_to_stars('5.9'), Decimal('3'))
        self.assertFalse(meets_captured_legacy_threshold('2.95', 6))
        self.assertTrue(meets_captured_legacy_threshold('3', 6))
        self.assertTrue(meets_captured_legacy_threshold('0', 0))
        with self.assertRaises(ValueError):
            meets_captured_legacy_threshold('2', 11)

    def test_all_ten_point_steps_preserve_existing_visible_stars(self):
        for tenth in range(101):
            score = Decimal(tenth) / Decimal(10)
            old_half_star_units = score.quantize(Decimal('1'), rounding=__import__('decimal').ROUND_HALF_UP)
            with self.subTest(score=score):
                self.assertEqual(historical_score_to_stars(score), old_half_star_units / Decimal(2))

    def test_all_legacy_profile_thresholds_map_to_whole_stars(self):
        self.assertEqual([historical_profile_minimum(value) for value in range(11)],
                         [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5])

    def test_invalid_inputs_are_rejected(self):
        for value in ('NaN', 'Infinity', True, 'not-a-number'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                rounded_star_score(value)
        for value in ('-0.1', '10.1'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                historical_score_to_stars(value)
        for value in ('-1', '11', '5.5'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                historical_profile_minimum(value)
