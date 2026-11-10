from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from jobs.models import JobSourceStatus, Vacancy
from matching.models import RUBRIC_VERSION, MatchingConfig, VacancyAnalysis
from profiles.models import Profile, ProfileRevision

from .models import AdminCommandRun, OperationalRun
from .services import begin_run, finish_run
from .tasks import cleanup_operational_history


class OperationalRunTests(TestCase):
    def test_successful_and_failed_attempts_are_saved_separately(self):
        success = begin_run(kind=OperationalRun.Kind.ANALYSIS, operation="vacancy_analysis")
        failure = begin_run(kind=OperationalRun.Kind.ANALYSIS, operation="vacancy_analysis")

        finish_run(success, status=OperationalRun.Status.SUCCEEDED, item_count=1)
        finish_run(failure, status=OperationalRun.Status.RETRYING, error_category="omniroute.http_503")

        self.assertEqual(OperationalRun.objects.count(), 2)
        self.assertGreaterEqual(success.duration_ms, 0)
        self.assertEqual(success.item_count, 1)
        self.assertEqual(failure.error_summary, "OmniRoute respondió HTTP 503.")
        self.assertNotIn("token", failure.error_summary.lower())

    def test_retention_removes_only_runs_older_than_ninety_days(self):
        now = timezone.now()
        old = OperationalRun.objects.create(
            kind=OperationalRun.Kind.ANALYSIS,
            operation="old",
            status=OperationalRun.Status.SUCCEEDED,
            started_at=now - timedelta(days=91),
        )
        recent = OperationalRun.objects.create(
            kind=OperationalRun.Kind.ANALYSIS,
            operation="recent",
            status=OperationalRun.Status.SUCCEEDED,
            started_at=now - timedelta(days=89),
        )

        result = cleanup_operational_history.run()

        self.assertEqual(result["deleted_runs"], 1)
        self.assertFalse(OperationalRun.objects.filter(pk=old.pk).exists())
        self.assertTrue(OperationalRun.objects.filter(pk=recent.pk).exists())

    def test_retention_closes_runs_left_in_progress_after_worker_shutdown(self):
        stale = OperationalRun.objects.create(
            kind=OperationalRun.Kind.ANALYSIS,
            operation="interrupted",
            started_at=timezone.now() - timedelta(minutes=21),
        )
        recent = OperationalRun.objects.create(
            kind=OperationalRun.Kind.ANALYSIS,
            operation="still-running",
            started_at=timezone.now() - timedelta(minutes=10),
        )

        result = cleanup_operational_history.run()

        stale.refresh_from_db()
        recent.refresh_from_db()
        self.assertEqual(result["interrupted_runs"], 1)
        self.assertEqual(stale.status, OperationalRun.Status.FAILED)
        self.assertEqual(stale.error_category, "execution_interrupted")
        self.assertTrue(stale.finished_at)
        self.assertEqual(recent.status, OperationalRun.Status.RUNNING)


class OperationalDashboardTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_superuser("operator", password="strong-pass")
        self.applicant = get_user_model().objects.create_user("applicant", password="strong-pass")

    def test_staff_can_view_period_metrics_and_pending_queue(self):
        now = timezone.now()
        first_run = OperationalRun.objects.create(
            kind=OperationalRun.Kind.ANALYSIS,
            operation="vacancy_analysis",
            status=OperationalRun.Status.SUCCEEDED,
            item_count=1,
            started_at=now - timedelta(days=8),
            finished_at=now - timedelta(days=8) + timedelta(seconds=2),
            duration_ms=2000,
        )
        OperationalRun.objects.create(
            kind=OperationalRun.Kind.INGESTION,
            operation="source_query",
            source="elempleo_co",
            status=OperationalRun.Status.SUCCEEDED,
            item_count=3,
            new_count=1,
            known_count=2,
            known_updated_count=1,
            known_unchanged_count=1,
            started_at=now - timedelta(hours=1),
            finished_at=now - timedelta(hours=1) + timedelta(seconds=1),
            duration_ms=1000,
        )
        OperationalRun.objects.create(
            kind=OperationalRun.Kind.INGESTION,
            operation="source_query",
            source="elempleo_co",
            status=OperationalRun.Status.SUCCEEDED,
            item_count=2,
            started_at=now - timedelta(hours=2),
            finished_at=now - timedelta(hours=2) + timedelta(seconds=1),
            duration_ms=1000,
        )
        OperationalRun.objects.create(
            kind=OperationalRun.Kind.ANALYSIS,
            operation="vacancy_analysis",
            status=OperationalRun.Status.FAILED,
            error_category="omniroute.http_401",
            error_summary="OmniRoute respondió HTTP 401.",
            item_count=0,
            started_at=now - timedelta(minutes=30),
            finished_at=now - timedelta(minutes=30) + timedelta(seconds=4),
            duration_ms=4000,
        )
        OperationalRun.objects.create(
            kind=OperationalRun.Kind.RECOVERY,
            operation="analysis_recovery",
            status=OperationalRun.Status.SUCCEEDED,
            item_count=2,
            started_at=now - timedelta(minutes=10),
            finished_at=now - timedelta(minutes=10) + timedelta(seconds=1),
            duration_ms=1000,
        )
        OperationalRun.objects.create(
            kind=OperationalRun.Kind.RECOVERY,
            operation="analysis_recovery_exhausted",
            status=OperationalRun.Status.FAILED,
            error_category="analysis.recovery_exhausted",
            error_summary="El análisis agotó sus recuperaciones automáticas.",
            item_count=1,
            started_at=now - timedelta(minutes=5),
            finished_at=now - timedelta(minutes=5) + timedelta(seconds=1),
            duration_ms=1000,
        )
        source_status = JobSourceStatus.objects.create(
            source="elempleo_co", available=True, last_checked_at=now - timedelta(hours=1),
            last_success_at=now - timedelta(hours=1), last_vacancy_count=3,
        )
        profile = Profile.objects.create(
            owner=self.applicant, search_phrases=["private CV sentinel"], locations=["Medellín"],
            cv_file="profiles/1/cv/v1.docx", revision_number=1,
        )
        revision = ProfileRevision.objects.create(
            profile=profile, version=1, search_phrases=profile.search_phrases,
            locations=profile.locations, cv_file_path=profile.cv_file.name,
        )
        vacancy = Vacancy.objects.create(
            source="elempleo_co", title="Analista", location="Medellín",
            original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-1",
        )
        config = MatchingConfig.objects.create(
            version=1, rubric_version=RUBRIC_VERSION, analysis_prompt="private prompt sentinel",
            organization_prompt="Organiza",
        )
        pending = VacancyAnalysis.objects.create(
            profile=profile, profile_revision=revision, vacancy=vacancy, matching_config=config,
        )
        VacancyAnalysis.objects.filter(pk=pending.pk).update(created_at=now - timedelta(hours=5))
        pending.refresh_from_db()
        replaced = VacancyAnalysis.objects.create(
            profile=profile, profile_revision=revision, vacancy=vacancy, matching_config=config,
            status=VacancyAnalysis.Status.SUPERSEDED,
        )
        VacancyAnalysis.objects.filter(pk=replaced.pk).update(updated_at=now - timedelta(days=2))
        self.client.force_login(self.staff)

        response = self.client.get(reverse("operations:dashboard"), {"period": "7d"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["period"], "7d")
        self.assertEqual(response.context["analysis"]["total"], 1)
        self.assertEqual(response.context["analysis"]["failed"], 1)
        self.assertEqual(response.context["analysis"]["failure_rate"], 100)
        self.assertEqual(response.context["analysis"]["average_duration"], 4000)
        self.assertEqual(response.context["recovery"]["succeeded"], 1)
        self.assertEqual(response.context["recovery"]["failed"], 1)
        self.assertEqual(response.context["recovery"]["items"], 3)
        self.assertEqual(response.context["ingestion"]["items"], 5)
        self.assertEqual(response.context["pending_count"], 1)
        self.assertEqual(response.context["oldest_pending"], pending.created_at)
        self.assertEqual(response.context["superseded_analyses"], 1)
        self.assertEqual(response.context["coverage_start"], first_run.started_at)
        self.assertEqual(response.context["source_rows"][0]["status"], source_status)
        self.assertEqual(response.context["source_rows"][0]["metrics"]["classified_queries"], 1)
        self.assertEqual(response.context["source_rows"][0]["metrics"]["new_items"], 1)
        self.assertEqual(response.context["source_rows"][0]["metrics"]["known_items"], 2)
        self.assertContains(response, "Nuevas / conocidas")
        self.assertContains(response, "Actualizadas")
        self.assertContains(response, "No disponible")
        self.assertContains(response, "Análisis pendientes")
        self.assertContains(response, "Recuperación de análisis")
        self.assertContains(response, "El análisis agotó sus recuperaciones automáticas.")
        self.assertContains(response, "OmniRoute respondió HTTP 401.")
        self.assertNotContains(response, "private CV sentinel")
        self.assertNotContains(response, "private prompt sentinel")

    def test_period_without_runs_shows_zero_metrics(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("operations:dashboard"), {"period": "24h"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["analysis"]["total"], 0)
        self.assertEqual(response.context["analysis"]["failure_rate"], 0)
        self.assertEqual(response.context["analysis"]["average_duration"], 0)
        self.assertIsNone(response.context["oldest_pending"])

    def test_applicant_cannot_view_operational_metrics(self):
        self.client.force_login(self.applicant)

        response = self.client.get(reverse("operations:dashboard"))

        self.assertEqual(response.status_code, 403)

    @patch("jobs.tasks.refresh_sources.delay")
    def test_staff_can_queue_only_the_allowlisted_refresh_command(self, refresh,):
        refresh.return_value.id = "task-123"
        self.client.force_login(self.staff)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("operations:run_command"), {"command": "refresh_sources"})

        command = AdminCommandRun.objects.get()
        self.assertRedirects(response, reverse("operations:dashboard"))
        self.assertEqual(command.requested_by, self.staff)
        self.assertEqual(command.status, AdminCommandRun.Status.QUEUED)
        self.assertEqual(command.task_id, "task-123")
        refresh.assert_called_once_with(command.pk)

    def test_applicant_cannot_queue_a_command(self):
        self.client.force_login(self.applicant)

        response = self.client.post(reverse("operations:run_command"), {"command": "refresh_sources"})

        self.assertEqual(response.status_code, 403)
        self.assertFalse(AdminCommandRun.objects.exists())

    def test_arbitrary_command_and_arguments_are_rejected(self):
        self.client.force_login(self.staff)

        invalid_name = self.client.post(reverse("operations:run_command"), {"command": "shell"})
        invalid_argument = self.client.post(
            reverse("operations:run_command"), {"command": "refresh_sources", "task": "custom"},
        )

        self.assertEqual(invalid_name.status_code, 400)
        self.assertEqual(invalid_argument.status_code, 400)
        self.assertFalse(AdminCommandRun.objects.exists())

    @patch("jobs.tasks.refresh_sources.delay")
    def test_second_manual_refresh_is_not_queued_while_first_is_active(self, refresh):
        self.client.force_login(self.staff)
        AdminCommandRun.objects.create(command="refresh_sources", requested_by=self.staff)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("operations:run_command"), {"command": "refresh_sources"})

        self.assertRedirects(response, reverse("operations:dashboard"))
        self.assertEqual(AdminCommandRun.objects.count(), 1)
        refresh.assert_not_called()


@override_settings(OMNIROUTE_BASE_URL="https://omniroute.test/v1", OMNIROUTE_MODEL="test-model")
class OmniRouteDiagnosticTests(TestCase):
    @patch("matching.client.requests.post")
    def test_http_errors_are_classified_without_logging_response_body(self, post):
        from requests import HTTPError
        from matching.client import OmniRouteError, request_model_keywords

        response = Mock()
        response.status_code = 401
        response.raise_for_status.side_effect = HTTPError(response=response)
        post.return_value = response

        with self.assertRaises(OmniRouteError) as caught:
            request_model_keywords(
                profile_text="private cv text", search_phrases=[], locations=[], remote_ok=False,
                prompt="private prompt", parameters={},
            )

        self.assertEqual(caught.exception.category, "omniroute.http_401")
        self.assertNotIn("private", str(caught.exception))

    @patch("matching.client.requests.post")
    def test_invalid_json_is_classified(self, post):
        from matching.client import OmniRouteError, request_model_keywords

        response = Mock()
        response.json.side_effect = ValueError("body includes sensitive content")
        post.return_value = response

        with self.assertRaises(OmniRouteError) as caught:
            request_model_keywords(
                profile_text="", search_phrases=[], locations=[], remote_ok=False, prompt="", parameters={},
            )

        self.assertEqual(caught.exception.category, "omniroute.invalid_json")
        self.assertNotIn("sensitive", str(caught.exception))
