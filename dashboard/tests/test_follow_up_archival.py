from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dashboard.models import VacancyFollowUp
from dashboard.tasks import archive_inactive_follow_ups
from jobs.models import Vacancy
from matching.models import RUBRIC_VERSION, MatchingConfig, VacancyAnalysis
from profiles.models import Profile
from profiles.tests.helpers import mark_tour_completed


class FollowUpArchivalTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("archive-owner", password="pass")
        self.other_user = user_model.objects.create_user("archive-other", password="pass")
        mark_tour_completed(self.user, self.other_user)
        self.profile = Profile.objects.create(
            owner=self.user, revision_number=1, cv_file="profiles/archive-owner/cv/v1.pdf"
        )
        self.other_profile = Profile.objects.create(
            owner=self.other_user, revision_number=1, cv_file="profiles/archive-other/cv/v1.pdf"
        )
        self.revision = self.profile.revisions.create(version=1)
        self.other_revision = self.other_profile.revisions.create(version=1)
        self.config = MatchingConfig.objects.create(
            version=1, rubric_version=RUBRIC_VERSION,
            analysis_prompt="Prompt", organization_prompt="Organiza",
        )

    def create_vacancy(self, slug, status, *, state_age_days=35, profile=None):
        profile = profile or self.profile
        revision = self.revision if profile == self.profile else self.other_revision
        vacancy = Vacancy.objects.create(
            source="elempleo_co",
            title=f"Vacante {slug}",
            original_url=f"https://jobs.example.test/{slug}",
        )
        analysis = VacancyAnalysis.objects.create(
            profile=profile,
            profile_revision=revision,
            vacancy=vacancy,
            matching_config=self.config,
            status=VacancyAnalysis.Status.COMPLETED,
            score=8,
            score_breakdown={"skills": {"score": 4}},
            completed_at=timezone.now() - timedelta(days=state_age_days),
        )
        follow_up = VacancyFollowUp.objects.create(
            profile=profile,
            vacancy=vacancy,
            status=status,
            state_changed_at=timezone.now() - timedelta(days=state_age_days),
        )
        return vacancy, analysis, follow_up

    def test_archives_old_states_without_deleting_vacancies_or_analyses(self):
        old_states = [
            VacancyFollowUp.Status.APPLIED,
            VacancyFollowUp.Status.IN_PROGRESS,
            VacancyFollowUp.Status.INTERVIEW,
            VacancyFollowUp.Status.FINALIZED,
            VacancyFollowUp.Status.DISCARDED,
        ]
        records = [self.create_vacancy(f"old-{status}", status) for status in old_states]

        result = archive_inactive_follow_ups.run()

        self.assertEqual(result["archived"], len(old_states))
        for vacancy, analysis, follow_up in records:
            follow_up.refresh_from_db()
            self.assertIsNotNone(follow_up.archived_at)
            self.assertTrue(Vacancy.objects.filter(pk=vacancy.pk).exists())
            self.assertTrue(VacancyAnalysis.objects.filter(pk=analysis.pk).exists())

    def test_keeps_recent_state_and_archive_is_isolated_between_profiles(self):
        recent, _analysis, recent_follow_up = self.create_vacancy(
            "recent", VacancyFollowUp.Status.APPLIED, state_age_days=29
        )
        shared = Vacancy.objects.create(
            source="elempleo_co", title="Compartida", original_url="https://jobs.example.test/shared-archive"
        )
        VacancyAnalysis.objects.create(
            profile=self.profile, profile_revision=self.revision, vacancy=shared,
            matching_config=self.config, status=VacancyAnalysis.Status.COMPLETED,
            score=8, score_breakdown={"skills": {"score": 4}},
        )
        VacancyAnalysis.objects.create(
            profile=self.other_profile, profile_revision=self.other_revision, vacancy=shared,
            matching_config=self.config, status=VacancyAnalysis.Status.COMPLETED,
            score=8, score_breakdown={"skills": {"score": 4}},
        )
        old_follow_up = VacancyFollowUp.objects.create(
            profile=self.profile, vacancy=shared, status=VacancyFollowUp.Status.APPLIED,
            state_changed_at=timezone.now() - timedelta(days=31),
        )
        other_follow_up = VacancyFollowUp.objects.create(
            profile=self.other_profile, vacancy=shared, status=VacancyFollowUp.Status.APPLIED,
            state_changed_at=timezone.now() - timedelta(days=2),
        )

        archive_inactive_follow_ups.run()

        recent_follow_up.refresh_from_db()
        old_follow_up.refresh_from_db()
        other_follow_up.refresh_from_db()
        self.assertIsNone(recent_follow_up.archived_at)
        self.assertIsNotNone(old_follow_up.archived_at)
        self.assertIsNone(other_follow_up.archived_at)
        self.assertTrue(Vacancy.objects.filter(pk=shared.pk).exists())

    def test_archived_follow_up_is_hidden_from_dashboard_and_counts_only_for_its_profile(self):
        vacancy, _analysis, follow_up = self.create_vacancy(
            "hidden", VacancyFollowUp.Status.PENDING, state_age_days=2
        )
        follow_up.archived_at = timezone.now()
        follow_up.save(update_fields=["archived_at"])
        other_analysis = VacancyAnalysis.objects.create(
            profile=self.other_profile,
            profile_revision=self.other_revision,
            vacancy=vacancy,
            matching_config=self.config,
            status=VacancyAnalysis.Status.COMPLETED,
            score=8,
            score_breakdown={"skills": {"score": 4}},
        )
        other_follow_up = VacancyFollowUp.objects.create(
            profile=self.other_profile, vacancy=vacancy, status=VacancyFollowUp.Status.APPLIED
        )
        self.client.force_login(self.user)

        home_response = self.client.get(reverse("dashboard:home"))
        pending_response = self.client.get(reverse("dashboard:pending"))

        self.assertNotContains(home_response, vacancy.title)
        self.assertEqual(home_response.context["follow_up_counts"][VacancyFollowUp.Status.PENDING], 0)
        self.assertEqual(pending_response.context["follow_up_counts"][VacancyFollowUp.Status.PENDING], 0)
        self.assertTrue(VacancyAnalysis.objects.filter(pk=other_analysis.pk).exists())
        self.assertIsNone(other_follow_up.archived_at)

        self.client.force_login(self.other_user)
        other_response = self.client.get(reverse("dashboard:home"), {"state": "applied"})
        self.assertContains(other_response, vacancy.title)
        self.assertEqual(other_response.context["follow_up_counts"][VacancyFollowUp.Status.APPLIED], 1)

    def test_repeated_archival_is_idempotent(self):
        _vacancy, _analysis, follow_up = self.create_vacancy("idempotent", VacancyFollowUp.Status.APPLIED)

        first = archive_inactive_follow_ups.run()
        archived_at = follow_up.__class__.objects.get(pk=follow_up.pk).archived_at
        second = archive_inactive_follow_ups.run()
        follow_up.refresh_from_db()

        self.assertEqual(first["archived"], 1)
        self.assertEqual(second["archived"], 0)
        self.assertEqual(follow_up.archived_at, archived_at)
