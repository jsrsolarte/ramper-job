from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from jobs.models import Vacancy
from matching.models import MatchingConfig, VacancyAnalysis
from profiles.models import Profile, ProfileRevision


class GeneratedStarScoreTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user('synthetic-star-score')
        profile = Profile.objects.create(owner=user, revision_number=1)
        revision = ProfileRevision.objects.create(profile=profile, version=1)
        vacancy = Vacancy.objects.create(source='test', title='Vacante sintética', original_url='https://example.test/star-score')
        config = MatchingConfig.objects.create(version=1, analysis_prompt='Prueba', organization_prompt='Prueba')
        self.analysis = VacancyAnalysis.objects.create(profile=profile, profile_revision=revision,
            vacancy=vacancy, matching_config=config, score=Decimal('6.5'))

    def test_old_profile_writes_generate_whole_star_minimum_without_overwriting_source(self):
        profile = self.analysis.profile
        for original, expected in enumerate([0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]):
            Profile.objects.filter(pk=profile.pk).update(min_score=original)
            profile.refresh_from_db()
            with self.subTest(original=original):
                self.assertEqual(profile.min_score, original)
                self.assertEqual(profile.min_score_stars, expected)

    def test_existing_score_is_preserved_and_stars_are_generated(self):
        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.score, Decimal('6.5'))
        self.assertEqual(self.analysis.score_stars, Decimal('3.5'))

    def test_old_worker_update_recalculates_stars_and_rollback_keeps_original(self):
        VacancyAnalysis.objects.filter(pk=self.analysis.pk).update(score=Decimal('5.9'))
        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.score, Decimal('5.9'))
        self.assertEqual(self.analysis.score_stars, Decimal('3.0'))

    def test_new_rubric_write_keeps_old_worker_scale_and_generated_star_score(self):
        from matching.schemas import save_validated_analysis

        config = self.analysis.matching_config
        config.rubric_version = 3
        config.parameters = {'rubric': {'critical_requirement_deduction': '1.0'}}
        config.save(update_fields=['rubric_version', 'parameters'])
        payload = {'rubric_version': 3, 'critical_requirements': [], 'reasons': [], 'gaps': [],
                   'score_breakdown': {
                       'skills': {'score': 1.25, 'status': 'parcial', 'evidence': 'Parcial'},
                       'experience': {'score': 1, 'status': 'cumple', 'evidence': 'Experiencia'},
                       'alignment': {'score': 1, 'status': 'cumple', 'evidence': 'Cargo'},
                       'education': {'score': 0.5, 'status': 'cumple', 'evidence': 'Estudios'},
                       'profile_criteria': {'score': 0.5, 'status': 'no_aplica', 'evidence': 'No aplica'},
                   }}
        save_validated_analysis(self.analysis, payload)
        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.score, Decimal('9.0'))
        self.assertEqual(self.analysis.score_stars, Decimal('4.5'))
        self.assertEqual(self.analysis.score_breakdown['skills']['score'], 1.25)

    def test_all_legacy_tenths_match_the_conversion_rule(self):
        from matching.score_scale import historical_score_to_stars

        for tenth in range(101):
            score = Decimal(tenth) / Decimal(10)
            VacancyAnalysis.objects.filter(pk=self.analysis.pk).update(score=score)
            self.analysis.refresh_from_db()
            with self.subTest(score=score):
                self.assertEqual(self.analysis.score_stars, historical_score_to_stars(score))

    def test_null_and_out_of_range_values_do_not_become_valid_stars(self):
        for value in (None, Decimal('10.1'), Decimal('-1')):
            with self.subTest(value=value):
                VacancyAnalysis.objects.filter(pk=self.analysis.pk).update(score=value)
                self.analysis.refresh_from_db()
                self.assertEqual(self.analysis.score, value)
                self.assertIsNone(self.analysis.score_stars)


class StarScoreMigrationTests(__import__('django.test', fromlist=['TransactionTestCase']).TransactionTestCase):
    def test_old_records_convert_without_modification_and_rollback_preserves_them(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor

        executor = MigrationExecutor(connection)
        other_leaves = [node for node in executor.loader.graph.leaf_nodes() if node[0] != 'matching']
        previous = other_leaves + [('matching', '0013_analysis_source_query')]
        current = other_leaves + [('matching', '0014_vacancyanalysis_score_stars')]
        executor.migrate(previous)
        old_apps = executor.loader.project_state(previous).apps
        User = old_apps.get_model('auth', 'User')
        Profile = old_apps.get_model('profiles', 'Profile')
        Revision = old_apps.get_model('profiles', 'ProfileRevision')
        Vacancy = old_apps.get_model('jobs', 'Vacancy')
        Config = old_apps.get_model('matching', 'MatchingConfig')
        Analysis = old_apps.get_model('matching', 'VacancyAnalysis')
        user = User.objects.create(username='migration-synthetic')
        profile = Profile.objects.create(owner_id=user.pk, revision_number=1)
        revision = Revision.objects.create(profile_id=profile.pk, version=1)
        vacancy = Vacancy.objects.create(source='test', title='Prueba', original_url='https://example.test/migration')
        config = Config.objects.create(version=1, analysis_prompt='Prueba', organization_prompt='Prueba')
        original = Analysis.objects.create(profile_id=profile.pk, profile_revision_id=revision.pk,
            vacancy_id=vacancy.pk, matching_config_id=config.pk, score=Decimal('6.5'),
            score_breakdown={'evidence': 'sintética'})
        try:
            executor = MigrationExecutor(connection)
            executor.migrate(current)
            new_apps = executor.loader.project_state(current).apps
            result = new_apps.get_model('matching', 'VacancyAnalysis').objects.get(pk=original.pk)
            self.assertEqual(result.score, Decimal('6.5'))
            self.assertEqual(result.score_stars, Decimal('3.5'))
            self.assertEqual(result.score_breakdown, {'evidence': 'sintética'})
            executor = MigrationExecutor(connection)
            executor.migrate(previous)
            restored = executor.loader.project_state(previous).apps.get_model('matching', 'VacancyAnalysis').objects.get(pk=original.pk)
            self.assertEqual(restored.score, Decimal('6.5'))
            self.assertEqual(restored.score_breakdown, {'evidence': 'sintética'})
        finally:
            MigrationExecutor(connection).migrate(current)
