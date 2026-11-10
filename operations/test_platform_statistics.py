from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dashboard.models import VacancyFollowUp
from jobs.models import Vacancy
from matching.models import AICallAttempt, MatchingConfig, VacancyAnalysis
from operations.platform_statistics import build_platform_statistics
from profiles.models import Profile, ProfileRevision


class PlatformStatisticsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser("owner", password="strong-admin-pass")
        self.applicant_a = User.objects.create_user("candidate-a", password="strong-pass")
        self.applicant_b = User.objects.create_user("candidate-b", password="strong-pass")
        self.profile_a = self._profile(self.applicant_a)
        self.profile_b = self._profile(self.applicant_b)
        self.config_v1 = self._config(version=1, rubric_version=1, is_active=True)
        self.config_v2 = self._config(version=2, rubric_version=2, is_active=False)

    def _profile(self, user):
        profile = Profile.objects.create(
            owner=user,
            search_phrases=["private search phrase"],
            locations=["Medellín"],
            revision_number=1,
        )
        ProfileRevision.objects.create(
            profile=profile,
            version=1,
            search_phrases=profile.search_phrases,
            locations=profile.locations,
        )
        return profile

    @staticmethod
    def _config(*, version, rubric_version, is_active):
        return MatchingConfig.objects.create(
            version=version,
            rubric_version=rubric_version,
            analysis_prompt="private prompt sentinel",
            organization_prompt="Organiza",
            is_active=is_active,
        )

    @staticmethod
    def _vacancy(external_id, *, availability=Vacancy.AvailabilityStatus.UNKNOWN):
        return Vacancy.objects.create(
            source="elempleo_co",
            external_id=external_id,
            title=f"Private vacancy title {external_id}",
            original_url=f"https://example.test/jobs/{external_id}",
            availability_status=availability,
        )

    @staticmethod
    def _analysis(profile, vacancy, config, score, *, status=VacancyAnalysis.Status.COMPLETED, created_at=None):
        completed_at = created_at or timezone.now()
        analysis = VacancyAnalysis.objects.create(
            profile=profile,
            profile_revision=profile.revisions.get(version=profile.revision_number),
            vacancy=vacancy,
            matching_config=config,
            status=status,
            score=Decimal(str(score)) if status == VacancyAnalysis.Status.COMPLETED else None,
            score_breakdown={"skills": {"score": 1}},
            completed_at=completed_at if status == VacancyAnalysis.Status.COMPLETED else None,
        )
        return analysis

    def test_tracking_counts_are_per_profile_vacancy_and_include_implicit_pending(self):
        shared = self._vacancy("shared")
        another = self._vacancy("another")
        VacancyFollowUp.objects.create(
            profile=self.profile_a, vacancy=shared, status=VacancyFollowUp.Status.APPLIED,
        )
        VacancyFollowUp.objects.create(
            profile=self.profile_b, vacancy=shared, status=VacancyFollowUp.Status.INTERVIEW,
        )
        self._analysis(self.profile_a, another, self.config_v1, 4)

        stats = build_platform_statistics()
        counts = {row["value"]: row["count"] for row in stats["tracking_states"]}

        self.assertEqual(counts[VacancyFollowUp.Status.APPLIED], 1)
        self.assertEqual(counts[VacancyFollowUp.Status.INTERVIEW], 1)
        self.assertEqual(counts[VacancyFollowUp.Status.PENDING], 1)
        self.assertEqual(stats["tracking_total"], 3)

    def test_archived_followups_are_not_in_the_current_cut(self):
        vacancy = self._vacancy("archived")
        VacancyFollowUp.objects.create(
            profile=self.profile_a,
            vacancy=vacancy,
            status=VacancyFollowUp.Status.DISCARDED,
            archived_at=timezone.now(),
        )

        stats = build_platform_statistics()
        counts = {row["value"]: row["count"] for row in stats["tracking_states"]}

        self.assertEqual(counts[VacancyFollowUp.Status.DISCARDED], 0)
        self.assertEqual(stats["tracking_total"], 0)

    def test_current_scores_are_deduplicated_and_split_by_rubric(self):
        now = timezone.now()
        first = self._vacancy("score-a")
        second = self._vacancy("score-b")
        third = self._vacancy("score-c")
        first_result = self._analysis(self.profile_a, first, self.config_v1, "2.5", created_at=now - timedelta(days=1))
        self._analysis(self.profile_b, first, self.config_v1, "10.0", created_at=now - timedelta(days=1))
        replaced = self._analysis(
            self.profile_a, second, self.config_v1, "1.0",
            status=VacancyAnalysis.Status.SUPERSEDED, created_at=now - timedelta(days=2),
        )
        self._analysis(self.profile_a, second, self.config_v2, "8.5", created_at=now - timedelta(days=1))
        old_outside_coverage = self._analysis(
            self.profile_b, third, self.config_v1, "9.0", created_at=now - timedelta(days=10),
        )
        AICallAttempt.objects.create(
            analysis=first_result,
            stage=AICallAttempt.Stage.SCORING,
            duration_ms=1,
            outcome=AICallAttempt.Outcome.SUCCEEDED,
        )
        AICallAttempt.objects.filter(analysis=first_result).update(created_at=now - timedelta(days=8))

        stats = build_platform_statistics(period="30d", now=now)
        distributions = {row["rubric_version"]: row for row in stats["score_distributions"]}

        self.assertFalse(stats["coverage_complete"])
        self.assertEqual(distributions[1]["sample_size"], 2)
        self.assertEqual(distributions[1]["median"], Decimal("6.25"))
        self.assertEqual(distributions[1]["bands"][2]["count"], 1)
        self.assertEqual(distributions[1]["bands"][9]["count"], 1)
        self.assertEqual(distributions[2]["sample_size"], 1)
        self.assertEqual(distributions[2]["median"], Decimal("8.50"))
        self.assertFalse(VacancyAnalysis.objects.filter(pk=replaced.pk, status=VacancyAnalysis.Status.COMPLETED).exists())
        self.assertTrue(VacancyAnalysis.objects.filter(pk=old_outside_coverage.pk).exists())

    def test_period_without_covered_scores_shows_empty_state_not_zero_bars(self):
        now = timezone.now()
        vacancy = self._vacancy("old-score")
        analysis = self._analysis(self.profile_a, vacancy, self.config_v1, 6, created_at=now - timedelta(days=3))
        AICallAttempt.objects.create(
            analysis=analysis,
            stage=AICallAttempt.Stage.SCORING,
            duration_ms=1,
            outcome=AICallAttempt.Outcome.SUCCEEDED,
        )

        stats = build_platform_statistics(period="24h", now=now)

        self.assertFalse(stats["has_score_data"])
        self.assertEqual(stats["score_distributions"], [])

    def test_format_failures_are_grouped_by_safe_category_period_stage_and_outcome(self):
        now = timezone.now()
        recent = self._analysis(self.profile_a, self._vacancy("invalid-recent"), self.config_v1, 0,
                                status=VacancyAnalysis.Status.PENDING)
        old = self._analysis(self.profile_a, self._vacancy("invalid-old"), self.config_v1, 0,
                             status=VacancyAnalysis.Status.PENDING)
        AICallAttempt.objects.create(analysis=recent, stage=AICallAttempt.Stage.SCORING, duration_ms=1,
                                     outcome=AICallAttempt.Outcome.FAILED, error_category="analysis.rubric.version")
        AICallAttempt.objects.filter(analysis=recent).update(created_at=now - timedelta(hours=2))
        AICallAttempt.objects.create(analysis=recent, stage=AICallAttempt.Stage.SCORING, duration_ms=1,
                                     outcome=AICallAttempt.Outcome.RETRYING, error_category="omniroute.invalid_json")
        AICallAttempt.objects.create(analysis=recent, stage=AICallAttempt.Stage.ORGANIZATION, duration_ms=1,
                                     outcome=AICallAttempt.Outcome.FAILED, error_category="analysis.rubric.version")
        AICallAttempt.objects.create(analysis=recent, stage=AICallAttempt.Stage.SCORING, duration_ms=1,
                                     outcome=AICallAttempt.Outcome.SUCCEEDED, error_category="analysis.rubric.version")
        AICallAttempt.objects.create(analysis=recent, stage=AICallAttempt.Stage.SCORING, duration_ms=1,
                                     outcome=AICallAttempt.Outcome.FAILED, error_category="analysis_invalid")
        AICallAttempt.objects.filter(analysis=recent).update(created_at=now - timedelta(hours=2))
        AICallAttempt.objects.create(analysis=old, stage=AICallAttempt.Stage.SCORING, duration_ms=1,
                                     outcome=AICallAttempt.Outcome.FAILED, error_category="analysis.rubric.version")
        AICallAttempt.objects.filter(analysis=old).update(created_at=now - timedelta(days=3))

        stats = build_platform_statistics(period="24h", now=now)
        counts = {row["code"]: row["count"] for row in stats["format_failures"]}

        self.assertEqual(counts, {
            "analysis.rubric.version": 1,
            "omniroute.invalid_json": 1,
            "analysis_invalid": 1,
        })
        self.assertTrue(stats["has_format_failures"])
        labels = {row["code"]: row["label"] for row in stats["format_failures"]}
        self.assertEqual(labels["omniroute.invalid_json"], "La respuesta no es JSON válido")
        self.assertEqual(labels["analysis_invalid"], "Formato inválido (registro histórico)")

    def test_admin_can_open_global_statistics_and_applicant_cannot(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("operations:platform_statistics"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seguimiento por perfil")
        self.assertContains(response, "Estadísticas globales")
        self.assertContains(response, "Fallos de formato del análisis")
        self.assertContains(response, "No hay fallos de formato registrados en este intervalo.")
        self.assertNotContains(response, "candidate-a")
        self.assertNotContains(response, "private search phrase")
        self.assertNotContains(response, "private prompt sentinel")
        self.assertNotContains(response, "Private vacancy title")

        self.client.force_login(self.applicant_a)
        response = self.client.get(reverse("operations:platform_statistics"))
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("candidate-b", response.content.decode())

    def test_admin_center_links_to_global_statistics(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("operations:admin_center"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("operations:platform_statistics"))
