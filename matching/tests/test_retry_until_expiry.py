from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from dashboard.models import VacancyFollowUp
from jobs.models import Vacancy
from matching.models import AICallAttempt, MatchingConfig, ProfileVacancyDiscovery, PROMPT_VERSION, RUBRIC_VERSION, VacancyAnalysis
from matching.recovery import reconcile_pending_analyses
from matching.tasks import create_analysis, schedule_legacy_analyses
from profiles.models import Profile, ProfileRevision


@override_settings(ANALYSIS_RECOVERY_STALE_SECONDS=60, ANALYSIS_RECOVERY_LEASE_SECONDS=120, ANALYSIS_RECOVERY_BATCH_SIZE=10)
class RetryUntilExpiryTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user('retry-user')
        self.profile = Profile.objects.create(owner=user, cv_file='cv.pdf', revision_number=1, locations=['Medellín'])
        ProfileRevision.objects.create(profile=self.profile, version=1, locations=['Medellín'], cv_file_path='cv.pdf')
        self.vacancy = Vacancy.objects.create(source='example', title='Analista', location='Medellín', original_url='https://example.com/job')
        self.config = MatchingConfig.objects.create(version=1, rubric_version=RUBRIC_VERSION, prompt_version=PROMPT_VERSION, analysis_prompt='a', organization_prompt='b')
        self.analysis = create_analysis(self.profile, self.vacancy, self.config)

    @patch('matching.recovery._dispatch_analysis')
    def test_failed_analysis_retries_beyond_previous_limit(self, dispatch):
        self.analysis.status = VacancyAnalysis.Status.FAILED
        self.analysis.recovery_count = 3
        self.analysis.last_enqueued_at = timezone.now() - timedelta(hours=2)
        self.analysis.save()
        with self.captureOnCommitCallbacks(execute=True):
            result = reconcile_pending_analyses()
        self.analysis.refresh_from_db()
        self.assertEqual(result['recovered'], 1)
        self.assertEqual(self.analysis.status, VacancyAnalysis.Status.PENDING)
        self.assertEqual(self.analysis.recovery_count, 4)
        dispatch.assert_called_once_with(self.analysis.pk)

    @patch('matching.recovery._dispatch_analysis')
    def test_expiry_is_per_profile_and_preserves_advanced_followup(self, dispatch):
        discovery = ProfileVacancyDiscovery.objects.get(profile=self.profile, vacancy=self.vacancy)
        discovery.first_found_at = timezone.now() - timedelta(days=8)
        discovery.save(update_fields=['first_found_at'])
        followup = VacancyFollowUp.objects.create(profile=self.profile, vacancy=self.vacancy, status=VacancyFollowUp.Status.APPLIED)
        result = reconcile_pending_analyses()
        self.analysis.refresh_from_db()
        followup.refresh_from_db()
        self.assertEqual(result['exhausted'], 1)
        self.assertEqual(self.analysis.status, VacancyAnalysis.Status.SUPERSEDED)
        self.assertEqual(followup.status, VacancyFollowUp.Status.APPLIED)
        self.assertTrue(Vacancy.objects.filter(pk=self.vacancy.pk).exists())
        dispatch.assert_not_called()

    def test_pending_page_counts_failed_and_retrying_calls(self):
        self.analysis.status = VacancyAnalysis.Status.FAILED
        self.analysis.save(update_fields=['status'])
        for outcome in (AICallAttempt.Outcome.FAILED, AICallAttempt.Outcome.RETRYING):
            AICallAttempt.objects.create(analysis=self.analysis, stage=AICallAttempt.Stage.SCORING, outcome=outcome, duration_ms=1)
        self.client.force_login(self.profile.owner)
        response = self.client.get(reverse('dashboard:pending'))
        self.assertContains(response, 'Intentos fallidos: 2')

    def test_first_discovery_survives_new_revision_and_expiry_is_per_profile(self):
        discovery = ProfileVacancyDiscovery.objects.get(profile=self.profile, vacancy=self.vacancy)
        first_found = timezone.now() - timedelta(days=8)
        discovery.first_found_at = first_found
        discovery.save(update_fields=['first_found_at'])
        self.profile.revision_number = 2
        self.profile.save(update_fields=['revision_number'])
        ProfileRevision.objects.create(profile=self.profile, version=2, locations=['Medellín'], cv_file_path='cv.pdf')
        other = Profile.objects.create(owner=get_user_model().objects.create_user('other-retry-user'))

        self.assertIsNone(create_analysis(self.profile, self.vacancy, self.config))
        discovery.refresh_from_db()
        self.assertEqual(discovery.first_found_at, first_found)
        self.assertEqual(VacancyFollowUp.objects.get(profile=self.profile, vacancy=self.vacancy).status, VacancyFollowUp.Status.DISCARDED)
        self.assertFalse(VacancyFollowUp.objects.filter(profile=other, vacancy=self.vacancy).exists())
        self.assertTrue(Vacancy.objects.filter(pk=self.vacancy.pk).exists())

    @patch('matching.tasks.analyze_vacancy_for_profile.delay')
    def test_failed_analysis_moves_to_new_active_configuration(self, dispatch):
        self.analysis.status = VacancyAnalysis.Status.FAILED
        self.analysis.save(update_fields=['status'])
        self.config.is_active = False
        self.config.save(update_fields=['is_active'])
        new_config = MatchingConfig.objects.create(
            version=2, rubric_version=RUBRIC_VERSION, prompt_version=PROMPT_VERSION,
            analysis_prompt='nuevo', organization_prompt='nuevo',
        )
        with self.captureOnCommitCallbacks(execute=True):
            queued = schedule_legacy_analyses.run()
        replacement = VacancyAnalysis.objects.get(pk=queued[0])
        self.assertEqual(replacement.matching_config, new_config)
        self.assertEqual(replacement.status, VacancyAnalysis.Status.PENDING)
        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, VacancyAnalysis.Status.FAILED)
        dispatch.assert_called_once_with(replacement.pk)
