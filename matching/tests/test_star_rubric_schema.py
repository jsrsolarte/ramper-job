from decimal import Decimal

from django.test import SimpleTestCase
from matching.schemas import InvalidAnalysisError, validate_analysis


class StarRubricSchemaTests(SimpleTestCase):
    def payload(self):
        return {
            'rubric_version': 3,
            'score_breakdown': {
                'skills': {'score': 2, 'status': 'cumple', 'evidence': 'Habilidades'},
                'experience': {'score': 1, 'status': 'cumple', 'evidence': 'Experiencia'},
                'alignment': {'score': 1, 'status': 'cumple', 'evidence': 'Cargo'},
                'education': {'score': 0.5, 'status': 'cumple', 'evidence': 'Estudios'},
                'profile_criteria': {'score': 0.5, 'status': 'no_aplica', 'evidence': 'No aplica'},
            },
            'critical_requirements': [], 'reasons': [], 'gaps': [],
        }

    def test_version_three_maximum_and_critical_deduction(self):
        data = self.payload()
        self.assertEqual(validate_analysis(data, rubric_version=3, critical_deduction='1')['score'], Decimal('5'))
        data['critical_requirements'] = [{'requirement': 'Licencia', 'status': 'contradicho', 'evidence': 'No cuenta con ella'}]
        self.assertEqual(validate_analysis(data, rubric_version=3, critical_deduction='1')['score'], Decimal('4'))

    def test_sum_and_deductions_round_only_after_all_criteria(self):
        data = self.payload()
        data['score_breakdown']['skills'] = {'score': 1.25, 'status': 'parcial', 'evidence': 'Parcial'}
        data['critical_requirements'] = [{'requirement': 'Licencia', 'status': 'contradicho', 'evidence': 'No cuenta con ella'}]
        self.assertEqual(validate_analysis(data, rubric_version=3, critical_deduction='1')['score'], Decimal('3.5'))

    def test_captured_threshold_uses_unrounded_total_before_half_star_rounding(self):
        data = self.payload()
        data['score_breakdown'] = {
            'skills': {'score': 1.45, 'status': 'parcial', 'evidence': 'Parcial'},
            'experience': {'score': 0.5, 'status': 'parcial', 'evidence': 'Parcial'},
            'alignment': {'score': 0.5, 'status': 'parcial', 'evidence': 'Parcial'},
            'education': {'score': 0.25, 'status': 'parcial', 'evidence': 'Parcial'},
            'profile_criteria': {'score': 0.25, 'status': 'parcial', 'evidence': 'Parcial'},
        }
        result = validate_analysis(data, rubric_version=3, critical_deduction='1')
        self.assertEqual(result['score'], Decimal('3'))
        self.assertEqual(result['threshold_score'], Decimal('5.90'))

    def test_rejects_values_exceeding_new_maximum_or_precision(self):
        for value in (2.1, 1.234):
            with self.subTest(value=value):
                data = self.payload()
                data['score_breakdown']['skills'] = {'score': value, 'status': 'parcial', 'evidence': 'Parcial'}
                with self.assertRaises(InvalidAnalysisError):
                    validate_analysis(data, rubric_version=3, critical_deduction='1')
