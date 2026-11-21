from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from jobs.connectors.base import JobListing
from jobs.models import JobSourceStatus, Vacancy
from jobs.tasks import refresh_periodic_sources, refresh_profile_sources, refresh_sources
from matching.models import PROMPT_VERSION, RUBRIC_VERSION, MatchingConfig, ProfileSearchTerms, ProfileVacancyDiscovery
from operations.models import (
    AdminCommandRun,
    OperationalRun,
    RefreshBatch,
    RefreshBatchProfile,
    RefreshLease,
    RefreshWorkItem,
    RefreshWorkProfile,
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
    @patch("jobs.tasks.automatic_searches_paused", return_value=False)
    def test_periodic_cycle_records_start_and_runs_global_refresh(self, is_quiet, run_refresh):
        started_at = timezone.now()
        with patch("operations.scheduling.timezone.now", return_value=started_at):
            result = refresh_periodic_sources.run()

        run_refresh.assert_called_once_with(origin="automatic")
        self.assertEqual(result, run_refresh.return_value)
        self.assertEqual(PeriodicRefreshState.objects.get(pk=1).last_started_at, started_at)

    @patch("jobs.tasks.refresh_sources")
    @patch("jobs.tasks.processing_is_paused", return_value=True)
    def test_periodic_cycle_does_not_advance_timestamp_while_globally_paused(self, is_paused, run_refresh):
        previous_start = timezone.now() - timedelta(hours=1)
        PeriodicRefreshState.objects.create(pk=1, last_started_at=previous_start)

        refresh_periodic_sources.run()

        is_paused.assert_called_once_with()
        run_refresh.assert_not_called()
        self.assertEqual(PeriodicRefreshState.objects.get(pk=1).last_started_at, previous_start)

    @patch("jobs.resumable.prepare_refresh_batch.delay")
    def test_manual_refresh_does_not_advance_periodic_timestamp(self, prepare_batch):
        previous_start = timezone.now() - timedelta(hours=1)
        PeriodicRefreshState.objects.create(pk=1, last_started_at=previous_start)

        refresh_sources.run()

        self.assertEqual(PeriodicRefreshState.objects.get(pk=1).last_started_at, previous_start)

    @patch("jobs.resumable.prepare_refresh_batch.delay")
    def test_profile_refresh_does_not_advance_periodic_timestamp(self, prepare_batch):
        previous_start = timezone.now() - timedelta(hours=1)
        PeriodicRefreshState.objects.create(pk=1, last_started_at=previous_start)

        refresh_profile_sources.run(self.profile.pk)

        self.assertEqual(PeriodicRefreshState.objects.get(pk=1).last_started_at, previous_start)

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

    def _advance_batch_to_work_item(self, profile_leases, command_id=None, origin=RefreshBatch.Origin.MANUAL):
        from jobs.resumable import prepare_refresh_batch, prepare_refresh_profile, plan_refresh_batch

        prepare_refresh_batch.run(profile_leases, command_run_id=command_id, origin=origin)
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

    @patch("jobs.tasks.refresh_shared_sources.delay")
    def test_scheduled_refresh_excludes_paused_profiles(self, refresh_shared):
        paused_user = get_user_model().objects.create_user("paused-member")
        paused_profile = Profile.objects.create(
            owner=paused_user,
            cv_file="profiles/paused/cv/v1.pdf",
            revision_number=1,
            search_enabled=False,
        )
        ProfileRevision.objects.create(profile=paused_profile, version=1, cv_file_path=paused_profile.cv_file.name)

        result = refresh_sources.run()

        self.assertEqual(result, {"scheduled_profiles": 1})
        leases = refresh_shared.call_args.args[0]
        self.assertEqual({int(profile_id) for profile_id in leases}, {self.profile.pk})
        self.assertFalse(RefreshLease.objects.filter(key=f"profile-refresh:{paused_profile.pk}").exists())

    @patch("jobs.tasks.refresh_sources.apply_async")
    @patch("jobs.tasks.processing_is_paused", return_value=True)
    def test_global_pause_still_defers_the_whole_search_cycle(self, is_paused, defer_cycle):
        result = refresh_sources.run()

        self.assertEqual(result, {"deferred": "processing_paused"})
        defer_cycle.assert_called_once()
        self.assertFalse(RefreshLease.objects.exists())

    @patch("jobs.tasks.automatic_searches_paused", return_value=True)
    @patch("jobs.tasks.refresh_shared_sources.delay")
    def test_automatic_cycle_is_deferred_in_quiet_window_but_manual_is_allowed(self, dispatch, is_quiet):
        automatic = refresh_sources.run(origin="automatic")
        self.assertEqual(automatic, {"deferred": "automatic_search_schedule"})
        dispatch.assert_not_called()

        manual = refresh_sources.run(origin="manual")
        self.assertEqual(manual["scheduled_profiles"], 1)
        dispatch.assert_called_once()
        self.assertEqual(dispatch.call_args.kwargs["origin"], "manual")

    @patch("jobs.resumable.prepare_refresh_batch.delay")
    def test_paused_profile_refresh_task_skips_before_acquiring_a_lease(self, prepare_batch):
        self.profile.search_enabled = False
        self.profile.save(update_fields=("search_enabled",))

        result = refresh_profile_sources.run(self.profile.pk)

        self.assertEqual(result, {"skipped": "profile_search_paused_or_incomplete"})
        prepare_batch.assert_not_called()
        self.assertFalse(RefreshLease.objects.filter(key=f"profile-refresh:{self.profile.pk}").exists())

    @patch("jobs.resumable.plan_refresh_batch.delay")
    @patch("jobs.resumable.get_profile_search_terms")
    def test_profile_paused_before_preparation_is_skipped_without_search_terms(self, get_terms, plan_batch):
        from django.utils import timezone
        from jobs.resumable import prepare_refresh_profile

        self.profile.search_enabled = False
        self.profile.save(update_fields=("search_enabled",))
        now = timezone.now()
        batch = RefreshBatch.objects.create(status=RefreshBatch.Status.RUNNING, started_at=now)
        profile_run = OperationalRun.objects.create(
            kind=OperationalRun.Kind.INGESTION,
            operation="profile_refresh",
            status=OperationalRun.Status.RUNNING,
            started_at=now,
        )
        batch_profile = RefreshBatchProfile.objects.create(
            batch=batch,
            profile=self.profile,
            profile_run=profile_run,
            lease_token="paused-profile-lease",
        )

        result = prepare_refresh_profile.run(batch_profile.pk)

        batch_profile.refresh_from_db()
        self.assertEqual(result, {"skipped": "profile_search_paused_or_inactive"})
        self.assertTrue(batch_profile.prepared_at)
        self.assertEqual(batch_profile.search_request, {})
        get_terms.assert_not_called()
        plan_batch.assert_called_once_with(batch.pk)

    @patch("jobs.resumable.process_refresh_work_item.apply_async")
    @patch("operations.parameters.processing_is_paused", return_value=True)
    @patch("jobs.resumable._configured_connectors")
    def test_queued_work_for_paused_profile_finishes_without_query_or_requeue_during_global_pause(
        self, configured, is_paused, requeue,
    ):
        from django.utils import timezone
        from jobs.resumable import process_refresh_work_item

        self.profile.search_enabled = False
        self.profile.save(update_fields=("search_enabled",))
        now = timezone.now()
        batch = RefreshBatch.objects.create(
            status=RefreshBatch.Status.RUNNING,
            started_at=now,
            planned_at=now,
        )
        profile_run = OperationalRun.objects.create(
            kind=OperationalRun.Kind.INGESTION,
            operation="profile_refresh",
            status=OperationalRun.Status.RUNNING,
            started_at=now,
        )
        batch_profile = RefreshBatchProfile.objects.create(
            batch=batch,
            profile=self.profile,
            profile_run=profile_run,
            lease_token="paused-profile-lease",
            prepared_at=now,
        )
        source_run = OperationalRun.objects.create(
            kind=OperationalRun.Kind.INGESTION,
            operation="source_query",
            source="test-source",
            status=OperationalRun.Status.RUNNING,
            started_at=now,
        )
        item = RefreshWorkItem.objects.create(
            batch=batch,
            source_run=source_run,
            source="test-source",
            identity="paused-query",
            status=RefreshWorkItem.Status.QUEUED,
        )
        from operations.models import RefreshWorkProfile
        RefreshWorkProfile.objects.create(work_item=item, batch_profile=batch_profile, revision_id=self.revision.pk)

        result = process_refresh_work_item.run(item.pk)

        item.refresh_from_db()
        self.assertEqual(result, {"skipped": "all_profiles_search_paused"})
        self.assertEqual(item.status, RefreshWorkItem.Status.SUCCEEDED)
        configured.assert_not_called()
        requeue.assert_not_called()

    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    @patch("jobs.resumable.save_listings")
    def test_shared_query_results_are_not_associated_to_profile_paused_mid_query(
        self, save_listings, schedule_analysis,
    ):
        from types import SimpleNamespace
        from django.utils import timezone
        from jobs.resumable import _persist_listing_chunk

        paused_user = get_user_model().objects.create_user("paused-shared-member")
        paused_profile = Profile.objects.create(
            owner=paused_user,
            cv_file="profiles/paused-shared/cv/v1.pdf",
            revision_number=1,
            search_enabled=False,
        )
        paused_revision = ProfileRevision.objects.create(
            profile=paused_profile,
            version=1,
            locations=["Medellín"],
            cv_file_path=paused_profile.cv_file.name,
        )
        now = timezone.now()
        batch = RefreshBatch.objects.create(
            status=RefreshBatch.Status.RUNNING,
            started_at=now,
            planned_at=now,
        )
        batch_profiles = []
        for profile, revision, token in (
            (self.profile, self.revision, "active-profile-lease"),
            (paused_profile, paused_revision, "paused-profile-lease"),
        ):
            profile_run = OperationalRun.objects.create(
                kind=OperationalRun.Kind.INGESTION,
                operation="profile_refresh",
                status=OperationalRun.Status.RUNNING,
                started_at=now,
            )
            batch_profiles.append(RefreshBatchProfile.objects.create(
                batch=batch,
                profile=profile,
                profile_run=profile_run,
                lease_token=token,
                prepared_at=now,
            ))
        source_run = OperationalRun.objects.create(
            kind=OperationalRun.Kind.INGESTION,
            operation="source_query",
            source="test-source",
            status=OperationalRun.Status.RUNNING,
            started_at=now,
        )
        item = RefreshWorkItem.objects.create(
            batch=batch,
            source_run=source_run,
            source="test-source",
            identity="shared-query",
            status=RefreshWorkItem.Status.RUNNING,
            lease_token="active-work-lease",
            lease_expires_at=now + timedelta(minutes=10),
            search_request={"matching_config_id": self.config.pk},
        )
        RefreshWorkProfile.objects.create(work_item=item, batch_profile=batch_profiles[0], revision_id=self.revision.pk)
        RefreshWorkProfile.objects.create(work_item=item, batch_profile=batch_profiles[1], revision_id=paused_revision.pk)
        vacancy = Vacancy.objects.create(
            source="test-source",
            external_id="shared-1",
            title="Analista de procesos",
            company="Empresa",
            location="Medellín",
            original_url="https://jobs.example.test/vacancy/shared-1",
        )
        save_listings.return_value = SimpleNamespace(
            vacancies=[vacancy],
            new_count=1,
            known_count=0,
            known_updated_count=0,
            known_unchanged_count=0,
        )

        with self.captureOnCommitCallbacks(execute=True):
            result = _persist_listing_chunk(item.pk, "active-work-lease", 0, [self._listing()])

        self.assertTrue(result)
        self.assertTrue(ProfileVacancyDiscovery.objects.filter(profile=self.profile, vacancy=vacancy).exists())
        self.assertFalse(ProfileVacancyDiscovery.objects.filter(profile=paused_profile, vacancy=vacancy).exists())
        schedule_analysis.assert_called_once()
        self.assertEqual(schedule_analysis.call_args.kwargs["profile_ids"], [self.profile.pk])

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
        detailed_listing = JobListing(
            **{**listing.__dict__, "raw_data": {"details_fetch": {"status": "confirmed"}}}
        )
        connector.fetch_details.return_value = [detailed_listing]
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
        self.assertEqual(sum(run.details_requested_count for run in source_runs), 1)
        self.assertEqual(sum(run.details_received_count for run in source_runs), 1)
        self.assertEqual(sum(run.details_reused_count for run in source_runs), len(work_items) - 1)
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
        self.assertEqual(prepare_batch.call_args.kwargs["origin"], RefreshBatch.Origin.AUTOMATIC)
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

    @patch("operations.scheduling.automatic_searches_paused", return_value=True)
    @patch("jobs.tasks.automatic_searches_paused", return_value=False)
    @patch("jobs.tasks.configured_connectors")
    @patch("jobs.tasks.refresh_shared_sources.delay")
    def test_automatic_durable_unit_waits_in_quiet_window(self, dispatch, configured, task_quiet, worker_quiet):
        from jobs.resumable import process_refresh_work_item

        configured.return_value = [Mock(source="test-source")]
        refresh_sources.run(origin="automatic")
        profile_leases = dispatch.call_args.args[0]
        _, _, work_items = self._advance_batch_to_work_item(
            profile_leases, origin=RefreshBatch.Origin.AUTOMATIC,
        )
        configured.reset_mock()

        with patch("operations.scheduling.automatic_searches_paused", return_value=True):
            result = process_refresh_work_item.run(work_items[0].pk)

        self.assertEqual(result, {"deferred": "automatic_search_schedule"})
        work_items[0].refresh_from_db()
        self.assertEqual(work_items[0].status, RefreshWorkItem.Status.QUEUED)
        configured.assert_not_called()
