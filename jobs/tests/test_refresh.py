from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from jobs.connectors.base import JobListing
from jobs.models import JobSourceStatus, Vacancy
from jobs.tasks import refresh_periodic_sources, refresh_profile_sources, refresh_sources
from matching.models import PROMPT_VERSION, RUBRIC_VERSION, MatchingConfig, ProfileSearchTerms
from operations.models import (
    AdminCommandRun,
    OperationalRun,
    RefreshBatch,
    RefreshBatchProfile,
    RefreshLease,
    RefreshWorkItem,
    PeriodicRefreshState,
)
from profiles.models import Profile, ProfileRevision


class RefreshTasksTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("member")
        self.profile = Profile.objects.create(
            owner=user,
            search_phrases=["Analista de procesos"],
            locations=["Medellín"],
            cv_file="profiles/1/cv/v1.pdf",
            revision_number=1,
        )
        self.revision = ProfileRevision.objects.create(
            profile=self.profile,
            version=1,
            search_phrases=["Analista de procesos"],
            locations=["Medellín"],
            cv_file_path=self.profile.cv_file.name,
        )
        self.config = MatchingConfig.objects.create(
            version=1,
            rubric_version=RUBRIC_VERSION,
            prompt_version=PROMPT_VERSION,
            search_prompt="Genera palabras clave",
            analysis_prompt="Analiza",
            organization_prompt="Organiza",
        )
        self.term_set = ProfileSearchTerms.objects.create(
            profile_revision=self.revision,
            matching_config=self.config,
            keywords=["procesos", "analista de procesos"],
        )

    @patch("jobs.tasks.refresh_sources")
    def test_periodic_refresh_records_its_start(self, run_refresh):
        started_at = timezone.now()
        with patch("operations.scheduling.timezone.now", return_value=started_at):
            refresh_periodic_sources.run()
        self.assertEqual(PeriodicRefreshState.objects.get(pk=1).last_started_at, started_at)
        run_refresh.assert_called_once_with()

    @patch("jobs.tasks.refresh_sources")
    @patch("jobs.tasks.processing_is_paused", return_value=True)
    def test_periodic_refresh_keeps_last_start_unchanged_when_paused(self, is_paused, run_refresh):
        last_started_at = timezone.now() - timedelta(hours=1)
        PeriodicRefreshState.objects.create(last_started_at=last_started_at)
        refresh_periodic_sources.run()
        self.assertEqual(PeriodicRefreshState.objects.get(pk=1).last_started_at, last_started_at)
        run_refresh.assert_called_once_with()

    @patch("jobs.tasks.refresh_shared_sources.delay")
    def test_bulk_refresh_excludes_profiles_with_search_paused(self, refresh_shared):
        paused_owner = get_user_model().objects.create_user("paused-member")
        paused_profile = Profile.objects.create(
            owner=paused_owner,
            search_enabled=False,
            cv_file="profiles/paused/cv/v1.pdf",
            revision_number=1,
        )
        ProfileRevision.objects.create(profile=paused_profile, version=1, cv_file_path=paused_profile.cv_file.name)
        result = refresh_sources.run()
        self.assertEqual(result["scheduled_profiles"], 1)
        leases = refresh_shared.call_args.args[0]
        self.assertEqual({int(profile_id) for profile_id in leases}, {self.profile.pk})

    @patch("jobs.resumable.prepare_refresh_batch.delay")
    def test_profile_refresh_skips_a_paused_profile_without_lease(self, prepare_batch):
        self.profile.search_enabled = False
        self.profile.save(update_fields=("search_enabled",))
        self.assertEqual(
            refresh_profile_sources.run(self.profile.pk),
            {"skipped": "profile_search_paused_or_incomplete"},
        )
        prepare_batch.assert_not_called()
        self.assertFalse(RefreshLease.objects.filter(key=f"profile-refresh:{self.profile.pk}").exists())

    def _listing(self):
        return JobListing(
            source="test-source",
            external_id="123",
            title="Analista de procesos",
            company="Empresa",
            location="Medellín",
            description="Descripción de la vacante",
            original_url="https://jobs.example.test/vacancy/123",
        )

    def _advance_batch_to_work_item(self, profile_leases, command_id=None):
        from jobs.resumable import prepare_refresh_batch, prepare_refresh_profile, plan_refresh_batch

        prepare_refresh_batch.run(profile_leases, command_run_id=command_id)
        batch = RefreshBatch.objects.latest("pk")
        batch_profile = RefreshBatchProfile.objects.get(batch=batch, profile=self.profile)
        prepare_refresh_profile.run(batch_profile.pk)
        plan_refresh_batch.run(batch.pk)
        return batch, batch_profile, list(RefreshWorkItem.objects.filter(batch=batch).order_by("pk"))

    @patch("jobs.tasks.refresh_shared_sources.delay")
    def test_scheduled_refresh_dispatches_active_profiles_as_one_batch(self, refresh_shared):
        second_user = get_user_model().objects.create_user("member2")
        second_profile = Profile.objects.create(
            owner=second_user,
            search_phrases=["Ingeniero de procesos"],
            locations=["Bogotá"],
            cv_file="profiles/2/cv/v1.pdf",
            revision_number=1,
        )
        ProfileRevision.objects.create(
            profile=second_profile,
            version=1,
            search_phrases=second_profile.search_phrases,
            locations=second_profile.locations,
            cv_file_path=second_profile.cv_file.name,
        )
        Profile.objects.create(owner=get_user_model().objects.create_user("empty"))

        result = refresh_sources.run()

        self.assertEqual(result, {"scheduled_profiles": 2})
        refresh_shared.assert_called_once()
        leases = refresh_shared.call_args.args[0]
        self.assertEqual({int(profile_id) for profile_id in leases}, {self.profile.pk, second_profile.pk})
        self.assertEqual(set(RefreshLease.objects.values_list("token", flat=True)), set(leases.values()))

    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    @patch("matching.services.request_model_title_preselection")
    @patch("jobs.tasks.configured_connectors")
    @patch("jobs.tasks.refresh_shared_sources.delay")
    def test_manual_refresh_runs_resumable_batch_and_records_safe_summary(
        self, dispatch, configured, preselect, schedule_analysis,
    ):
        command = AdminCommandRun.objects.create(command="refresh_sources", requested_by=self.profile.owner)
        listing = self._listing()
        connector = Mock(source="test-source", status_message="")
        connector.fetch_titles.return_value = [listing]
        connector.fetch_details.return_value = [listing]
        configured.return_value = [connector]
        preselect.return_value = Mock(
            listings=[listing],
            discarded_count=0,
            input_tokens=12,
        )

        self.assertEqual(refresh_sources.run(command.pk), {"scheduled_profiles": 1})
        leases = dispatch.call_args.args[0]
        self.assertEqual(dispatch.call_args.kwargs["command_run_id"], command.pk)
        batch, batch_profile, work_items = self._advance_batch_to_work_item(leases, command.pk)

        from jobs.resumable import process_refresh_work_item

        with self.captureOnCommitCallbacks(execute=True):
            for work_item in work_items:
                process_refresh_work_item.run(work_item.pk)

        command.refresh_from_db()
        batch.refresh_from_db()
        batch_profile.refresh_from_db()
        for work_item in work_items:
            work_item.refresh_from_db()
        source_runs = OperationalRun.objects.filter(refresh_work_items__batch=batch, operation="source_query")
        self.assertEqual(command.status, AdminCommandRun.Status.SUCCEEDED)
        self.assertEqual(command.completed_profiles, 1)
        self.assertEqual(
            command.source_results["test-source"],
            {"queries": len(work_items), "vacancies": 1, "failures": 0},
        )
        self.assertEqual(batch.status, RefreshBatch.Status.SUCCEEDED)
        self.assertTrue(batch_profile.finished_at)
        self.assertTrue(all(item.status == RefreshWorkItem.Status.SUCCEEDED for item in work_items))
        self.assertEqual(source_runs.count(), len(work_items))
        for source_run in source_runs:
            self.assertEqual(source_run.listing_count, 1)
            self.assertEqual(source_run.title_kept_count, 1)
            self.assertEqual(source_run.details_requested_count, 1)
            self.assertEqual(source_run.details_received_count, 1)
        self.assertEqual(Vacancy.objects.count(), 1)
        self.assertTrue(JobSourceStatus.objects.get(source="test-source").available)
        self.assertEqual(schedule_analysis.call_count, len(work_items))

    @patch("jobs.resumable.prepare_refresh_batch.delay")
    def test_profile_refresh_only_schedules_durable_batch(self, prepare_batch):
        result = refresh_profile_sources.run(self.profile.pk)

        self.assertEqual(result, {"scheduled_profiles": 1})
        prepare_batch.assert_called_once()
        profile_leases = prepare_batch.call_args.args[0]
        self.assertEqual(set(profile_leases), {str(self.profile.pk)})
        self.assertTrue(RefreshLease.objects.filter(key=f"profile-refresh:{self.profile.pk}").exists())

    @patch("jobs.resumable.prepare_refresh_batch.delay")
    def test_profile_refresh_does_not_dispatch_when_another_lease_is_claimed(self, prepare_batch):
        from operations.services import acquire_refresh_lease, claim_refresh_lease

        key = f"profile-refresh:{self.profile.pk}"
        token = acquire_refresh_lease(key)
        self.assertTrue(claim_refresh_lease(key, token))

        result = refresh_profile_sources.run(self.profile.pk)

        self.assertEqual(result, {"skipped": "already_running"})
        prepare_batch.assert_not_called()
        self.assertEqual(RefreshLease.objects.get(key=key).token, token)
