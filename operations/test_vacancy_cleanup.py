from datetime import time
from types import SimpleNamespace
from unittest.mock import patch

from celery.exceptions import Ignore
from django.contrib.auth import get_user_model
from django.core.signing import BadSignature
from django.test import TestCase
from django.urls import reverse

from dashboard.models import VacancyFollowUp
from jobs.models import ManualVacancySubmission, Vacancy
from matching.models import MatchingConfig
from operations.models import (
    AutomaticSearchSchedule,
    AdminAuditEvent,
    OperationalRun,
    OperationalParameter,
    VacancyCleanupOperation,
    VacancyDataCoverage,
    VacancyDataGeneration,
)
from operations.signals import reject_stale_vacancy_task
from profiles.models import Profile, ProfileRevision
from operations.vacancy_cleanup import (
    CleanupError,
    cleanup_preview_counts,
    execute_vacancy_cleanup,
    issue_cleanup_confirmation,
    start_vacancy_cleanup,
)


class VacancyCleanupTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="cleanup-admin", email="cleanup@example.test", password="test-pass",
        )

    @patch("operations.tasks.execute_vacancy_cleanup_task.delay")
    def test_cleanup_deletes_only_vacancy_data_preserves_profiles_and_restores_pause(self, _dispatch):
        profile = Profile.objects.create(owner=self.admin)
        profile.cv_file = "profiles/1/cv/v1.pdf"
        profile.revision_number = 1
        profile.save(update_fields=("cv_file", "revision_number", "updated_at"))
        revision = ProfileRevision.objects.create(profile=profile, version=1, cv_file_path=profile.cv_file.name)
        config = MatchingConfig.objects.create(
            version=77, analysis_prompt="synthetic", organization_prompt="synthetic",
        )
        protected_parameter = OperationalParameter.objects.create(key="auto_discard_days", value=7)
        vacancy = Vacancy.objects.create(
            source="magneto_co", title="Synthetic vacancy", original_url="https://example.test/job/1",
        )
        VacancyFollowUp.objects.create(profile=profile, vacancy=vacancy)
        ManualVacancySubmission.objects.create(
            submitted_by=self.admin, original_url="https://example.test/job/2", title="Synthetic manual",
        )
        AutomaticSearchSchedule.objects.create(pk=1, enabled=True, starts_at=time(21), ends_at=time(7))
        token = issue_cleanup_confirmation(cleanup_preview_counts())
        operation = start_vacancy_cleanup(actor=self.admin, token=token)

        result = execute_vacancy_cleanup(operation.pk)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(Vacancy.objects.count(), 0)
        self.assertEqual(VacancyFollowUp.objects.count(), 0)
        self.assertEqual(ManualVacancySubmission.objects.count(), 0)
        self.assertTrue(Profile.objects.filter(pk=profile.pk).exists())
        profile.refresh_from_db()
        self.assertEqual(profile.cv_file.name, "profiles/1/cv/v1.pdf")
        self.assertTrue(ProfileRevision.objects.filter(pk=revision.pk).exists())
        self.assertTrue(MatchingConfig.objects.filter(pk=config.pk).exists())
        self.assertTrue(OperationalParameter.objects.filter(pk=protected_parameter.pk).exists())
        self.assertTrue(get_user_model().objects.filter(pk=self.admin.pk).exists())
        self.assertTrue(AutomaticSearchSchedule.objects.filter(pk=1).exists())
        self.assertFalse(bool(OperationalParameter.objects.get(key="processing_paused").value))
        self.assertTrue(VacancyDataCoverage.objects.filter(pk=1, cleanup_operation=operation).exists())
        operation.refresh_from_db()
        self.assertEqual(operation.requested_by, self.admin)
        self.assertEqual(operation.counts["vacancies"], 1)
        self.assertEqual(AdminAuditEvent.objects.filter(
            action__in=(AdminAuditEvent.Action.PROCESSING_PAUSED, AdminAuditEvent.Action.PROCESSING_RESUMED),
        ).count(), 2)
        control = VacancyDataGeneration.objects.get(pk=1)
        self.assertFalse(control.cleanup_active)
        self.assertEqual(control.generation, operation.generation + 1)

    @patch("operations.tasks.execute_vacancy_cleanup_task.apply_async")
    @patch("operations.tasks.execute_vacancy_cleanup_task.delay")
    def test_active_work_delays_deletion_and_keeps_system_paused(self, _dispatch, _retry):
        token = issue_cleanup_confirmation(cleanup_preview_counts())
        operation = start_vacancy_cleanup(actor=self.admin, token=token)
        OperationalRun.objects.create(
            kind=OperationalRun.Kind.INGESTION, operation="in-progress",
            status=OperationalRun.Status.RUNNING,
        )
        result = execute_vacancy_cleanup(operation.pk)
        operation.refresh_from_db()
        self.assertEqual(result["status"], "waiting")
        self.assertEqual(operation.status, VacancyCleanupOperation.Status.WAITING)
        self.assertTrue(VacancyDataGeneration.objects.get(pk=1).cleanup_active)
        self.assertTrue(bool(OperationalParameter.objects.get(key="processing_paused").value))
        self.assertEqual(OperationalRun.objects.count(), 1)

    @patch("operations.tasks.execute_vacancy_cleanup_task.delay")
    def test_second_cleanup_is_rejected_while_one_is_active(self, _dispatch):
        first = start_vacancy_cleanup(
            actor=self.admin, token=issue_cleanup_confirmation(cleanup_preview_counts()),
        )
        with self.assertRaises(CleanupError) as error:
            start_vacancy_cleanup(
                actor=self.admin, token=issue_cleanup_confirmation(cleanup_preview_counts()),
            )
        self.assertEqual(error.exception.code, "cleanup_active")
        self.assertEqual(VacancyCleanupOperation.objects.count(), 1)
        self.assertTrue(VacancyDataGeneration.objects.get(pk=1).active_operation_id == first.pk)

    @patch("operations.tasks.execute_vacancy_cleanup_task.apply_async")
    @patch("operations.tasks.execute_vacancy_cleanup_task.delay")
    def test_active_work_timeout_aborts_without_deleting_and_stays_paused(self, _dispatch, _retry):
        operation = start_vacancy_cleanup(
            actor=self.admin, token=issue_cleanup_confirmation(cleanup_preview_counts()),
        )
        OperationalRun.objects.create(
            kind=OperationalRun.Kind.ANALYSIS, operation="still-running",
            status=OperationalRun.Status.RUNNING,
        )
        operation.attempt_count = 119
        operation.save(update_fields=("attempt_count",))
        result = execute_vacancy_cleanup(operation.pk)
        operation.refresh_from_db()
        self.assertEqual(result["category"], "active_work_timeout")
        self.assertEqual(operation.status, VacancyCleanupOperation.Status.FAILED)
        self.assertTrue(VacancyDataGeneration.objects.get(pk=1).cleanup_active)
        self.assertTrue(bool(OperationalParameter.objects.get(key="processing_paused").value))

    @patch("operations.tasks.execute_vacancy_cleanup_task.delay")
    def test_transaction_failure_rolls_back_data_and_leaves_pause_for_recovery(self, _dispatch):
        vacancy = Vacancy.objects.create(
            source="magneto_co", title="Retained on rollback", original_url="https://example.test/job/4",
        )
        operation = start_vacancy_cleanup(
            actor=self.admin, token=issue_cleanup_confirmation(cleanup_preview_counts()),
        )
        with patch("operations.vacancy_cleanup._delete_scoped_data", side_effect=RuntimeError("synthetic")):
            result = execute_vacancy_cleanup(operation.pk)
        operation.refresh_from_db()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(operation.status, VacancyCleanupOperation.Status.FAILED)
        self.assertTrue(Vacancy.objects.filter(pk=vacancy.pk).exists())
        self.assertTrue(VacancyDataGeneration.objects.get(pk=1).cleanup_active)
        self.assertTrue(bool(OperationalParameter.objects.get(key="processing_paused").value))

    @patch("operations.tasks.execute_vacancy_cleanup_task.delay")
    def test_pause_requested_during_cleanup_is_preserved(self, _dispatch):
        operation = start_vacancy_cleanup(
            actor=self.admin, token=issue_cleanup_confirmation(cleanup_preview_counts()),
        )
        from operations.parameters import set_processing_paused
        set_processing_paused(actor=self.admin, paused=False)
        set_processing_paused(actor=self.admin, paused=True)
        self.assertEqual(execute_vacancy_cleanup(operation.pk)["status"], "completed")
        self.assertTrue(bool(OperationalParameter.objects.get(key="processing_paused").value))

    @patch("operations.tasks.execute_vacancy_cleanup_task.delay")
    def test_completed_operation_can_be_replayed_without_deleting_again(self, _dispatch):
        operation = start_vacancy_cleanup(
            actor=self.admin, token=issue_cleanup_confirmation(cleanup_preview_counts()),
        )
        result = execute_vacancy_cleanup(operation.pk)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(execute_vacancy_cleanup(operation.pk)["status"], "missing_or_completed")

    def test_preview_token_is_invalidated_when_data_scope_changes(self):
        token = issue_cleanup_confirmation(cleanup_preview_counts())
        Vacancy.objects.create(
            source="magneto_co", title="Synthetic vacancy", original_url="https://example.test/job/3",
        )
        with self.assertRaises(CleanupError) as error:
            start_vacancy_cleanup(actor=self.admin, token=token)
        self.assertEqual(error.exception.code, "preview_changed")
        self.assertFalse(VacancyDataGeneration.objects.filter(pk=1).exists())

    @patch("operations.tasks.execute_vacancy_cleanup_task.delay")
    def test_single_use_confirmation_cannot_start_a_second_operation(self, _dispatch):
        token = issue_cleanup_confirmation(cleanup_preview_counts())
        operation = start_vacancy_cleanup(actor=self.admin, token=token)
        self.assertEqual(execute_vacancy_cleanup(operation.pk)["status"], "completed")
        with self.assertRaises(CleanupError) as error:
            start_vacancy_cleanup(actor=self.admin, token=token)
        self.assertEqual(error.exception.code, "confirmation_used")

    def test_expired_confirmation_is_rejected(self):
        with patch("operations.vacancy_cleanup.signing.loads", side_effect=BadSignature("expired")):
            with self.assertRaises(CleanupError) as error:
                start_vacancy_cleanup(actor=self.admin, token="expired")
        self.assertEqual(error.exception.code, "confirmation_expired")

    def test_old_and_during_cleanup_tasks_are_rejected_by_generation(self):
        control = VacancyDataGeneration.objects.create(pk=1, generation=3, cleanup_active=False)
        stale_task = SimpleNamespace(
            name="matching.tasks.analyze_vacancy_for_profile",
            request=SimpleNamespace(headers={"ramper_data_generation": 1}),
        )
        with self.assertRaises(Ignore):
            reject_stale_vacancy_task(sender=None, task=stale_task)
        control.cleanup_active = True
        control.save(update_fields=("cleanup_active",))
        current_task = SimpleNamespace(
            name="jobs.tasks.refresh_periodic_sources",
            request=SimpleNamespace(headers={"ramper_data_generation": 3}),
        )
        with self.assertRaises(Ignore):
            reject_stale_vacancy_task(sender=None, task=current_task)


class VacancyCleanupViewTests(TestCase):
    def test_preview_is_admin_only_and_does_not_mutate_data(self):
        user = get_user_model().objects.create_user(username="applicant", password="test-pass")
        self.client.force_login(user)
        response = self.client.get(reverse("operations:vacancy_cleanup"))
        self.assertEqual(response.status_code, 403)
        self.assertFalse(VacancyDataGeneration.objects.exists())

    def test_missing_explicit_phrase_does_not_start_operation(self):
        admin = get_user_model().objects.create_superuser(
            username="confirmation-admin", email="confirm@example.test", password="test-pass",
        )
        self.client.force_login(admin)
        response = self.client.post(reverse("operations:vacancy_cleanup"), {
            "confirmation_token": "anything", "confirmation_phrase": "yes",
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(VacancyDataGeneration.objects.exists())
        self.assertFalse(VacancyCleanupOperation.objects.exists())

    def test_admin_preview_is_read_only_and_warns_about_missing_backups(self):
        admin = get_user_model().objects.create_superuser(
            username="preview-admin", email="preview@example.test", password="test-pass",
        )
        self.client.force_login(admin)
        response = self.client.get(reverse("operations:vacancy_cleanup"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No hay respaldos configurados")
        self.assertFalse(VacancyDataGeneration.objects.exists())

