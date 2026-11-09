from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from dashboard.models import VacancyFollowUp
from dashboard.tasks import discard_stale_recommendations
from jobs.models import Vacancy
from matching.models import RUBRIC_VERSION, MatchingConfig, VacancyAnalysis
from profiles.models import Profile
from profiles.tests.helpers import mark_tour_completed


class DiscardStaleRecommendationsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("auto-discard-owner")
        mark_tour_completed(self.user)
        self.profile = Profile.objects.create(owner=self.user, revision_number=1)
        self.revision = self.profile.revisions.create(version=1)
        self.config = MatchingConfig.objects.create(
            version=1,
            rubric_version=RUBRIC_VERSION,
            analysis_prompt="Prompt",
            organization_prompt="Organiza",
        )
        self.vacancy = self.make_vacancy("Analista de procesos", "auto-discard")
        self.analysis = self.make_analysis(self.profile, self.revision, self.vacancy)

    @staticmethod
    def make_vacancy(title, slug):
        return Vacancy.objects.create(
            source="elempleo_co",
            title=title,
            original_url=f"https://jobs.example.test/{slug}",
        )

    def make_analysis(self, profile, revision, vacancy, *, completed_at=None):
        return VacancyAnalysis.objects.create(
            profile=profile,
            profile_revision=revision,
            vacancy=vacancy,
            matching_config=self.config,
            status=VacancyAnalysis.Status.COMPLETED,
            score=8,
            score_breakdown={"skills": {"score": 4}},
            completed_at=completed_at or timezone.now() - timedelta(days=8),
        )

    def test_discards_stale_recommendation_and_preserves_pending_as_previous_state(self):
        result = discard_stale_recommendations.run()

        follow_up = VacancyFollowUp.objects.get(profile=self.profile, vacancy=self.vacancy)
        self.assertEqual(result["discarded"], 1)
        self.assertEqual(follow_up.status, VacancyFollowUp.Status.DISCARDED)
        self.assertEqual(follow_up.previous_status, VacancyFollowUp.Status.PENDING)
        self.assertGreater(follow_up.state_changed_at, self.analysis.completed_at)

    def test_does_not_discard_recent_or_already_advanced_recommendations(self):
        recent = self.make_vacancy("Recomendación reciente", "auto-discard-recent")
        self.make_analysis(
            self.profile, self.revision, recent, completed_at=timezone.now() - timedelta(days=3)
        )
        advanced = self.make_vacancy("Vacante aplicada", "auto-discard-applied")
        self.make_analysis(self.profile, self.revision, advanced)
        VacancyFollowUp.objects.create(
            profile=self.profile,
            vacancy=advanced,
            status=VacancyFollowUp.Status.APPLIED,
        )

        result = discard_stale_recommendations.run()

        self.assertEqual(result["discarded"], 1)
        self.assertFalse(VacancyFollowUp.objects.filter(profile=self.profile, vacancy=recent).exists())
        applied = VacancyFollowUp.objects.get(profile=self.profile, vacancy=advanced)
        self.assertEqual(applied.status, VacancyFollowUp.Status.APPLIED)

    def test_age_is_isolated_per_profile_and_restore_restarts_the_period(self):
        other_user = get_user_model().objects.create_user("auto-discard-other")
        other_profile = Profile.objects.create(owner=other_user, revision_number=1)
        other_revision = other_profile.revisions.create(version=1)
        self.make_analysis(other_profile, other_revision, self.vacancy)
        own_follow_up = VacancyFollowUp.objects.create(
            profile=self.profile,
            vacancy=self.vacancy,
            status=VacancyFollowUp.Status.PENDING,
            state_changed_at=timezone.now() - timedelta(days=1),
        )

        result = discard_stale_recommendations.run()

        self.assertEqual(result["discarded"], 1)
        own_follow_up.refresh_from_db()
        self.assertEqual(own_follow_up.status, VacancyFollowUp.Status.PENDING)
        other_follow_up = VacancyFollowUp.objects.get(profile=other_profile, vacancy=self.vacancy)
        self.assertEqual(other_follow_up.status, VacancyFollowUp.Status.DISCARDED)

        # Restoring uses the normal dashboard transition and starts a fresh pending period.
        from django.urls import reverse

        restore_vacancy = self.make_vacancy("Vacante para restaurar", "auto-discard-restore")
        self.make_analysis(self.profile, self.revision, restore_vacancy)
        discard_stale_recommendations.run()
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("dashboard:update_follow_up", args=[restore_vacancy.pk]), {"status": "restore"}
        )
        self.assertEqual(response.status_code, 302)
        restored_follow_up = VacancyFollowUp.objects.get(profile=self.profile, vacancy=restore_vacancy)
        self.assertEqual(restored_follow_up.status, VacancyFollowUp.Status.PENDING)
        self.assertGreater(restored_follow_up.state_changed_at, timezone.now() - timedelta(minutes=1))

        result = discard_stale_recommendations.run()
        self.assertEqual(result["discarded"], 0)
        restored_follow_up.refresh_from_db()
        self.assertEqual(restored_follow_up.status, VacancyFollowUp.Status.PENDING)

    def test_repeated_execution_is_idempotent(self):
        first = discard_stale_recommendations.run()
        second = discard_stale_recommendations.run()

        self.assertEqual(first["discarded"], 1)
        self.assertEqual(second["discarded"], 0)
        self.assertEqual(VacancyFollowUp.objects.filter(profile=self.profile).count(), 1)
