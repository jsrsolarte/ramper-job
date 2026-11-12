from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from operations.models import (
    OperationalRun,
    RefreshBatch,
    RefreshBatchProfile,
    RefreshWorkItem,
    RefreshWorkProfile,
)
from operations.tasks import reconcile_refresh_work
from profiles.models import Profile


class RefreshWorkReconciliationTests(TestCase):
    def make_running_item(self, *, attempts=0, heartbeat_age_minutes=25, lease_expired=True):
        now = timezone.now()
        user = get_user_model().objects.create_user(f"member-{attempts}-{heartbeat_age_minutes}")
        profile = Profile.objects.create(owner=user, revision_number=1)
        old = now - timedelta(minutes=heartbeat_age_minutes)
        batch = RefreshBatch.objects.create(
            status=RefreshBatch.Status.RUNNING,
            started_at=old,
            planned_at=old,
            heartbeat_at=old,
        )
        profile_run = OperationalRun.objects.create(
            kind=OperationalRun.Kind.INGESTION,
            operation="profile_refresh",
            status=OperationalRun.Status.RUNNING,
            started_at=old,
        )
        batch_profile = RefreshBatchProfile.objects.create(
            batch=batch,
            profile=profile,
            profile_run=profile_run,
            lease_token=f"profile-lease-{attempts}",
            prepared_at=old,
        )
        source_run = OperationalRun.objects.create(
            kind=OperationalRun.Kind.INGESTION,
            operation="source_query",
            source="computrabajo_co",
            status=OperationalRun.Status.RUNNING,
            started_at=old,
        )
        item = RefreshWorkItem.objects.create(
            batch=batch,
            source_run=source_run,
            source="computrabajo_co",
            identity=f"identity-{attempts}-{heartbeat_age_minutes}",
            status=RefreshWorkItem.Status.RUNNING,
            attempts=attempts,
            lease_token="stale-work-lease",
            lease_expires_at=old if lease_expired else now + timedelta(minutes=5),
            heartbeat_at=old,
        )
        RefreshWorkProfile.objects.create(
            work_item=item,
            batch_profile=batch_profile,
            revision_id=1,
        )
        return item, source_run, profile_run, batch_profile

    @patch("jobs.resumable.process_refresh_work_item.delay")
    def test_stale_unit_without_live_lease_is_requeued_idempotently(self, dispatch):
        item, source_run, profile_run, batch_profile = self.make_running_item()

        result = reconcile_refresh_work.run()

        item.refresh_from_db()
        source_run.refresh_from_db()
        profile_run.refresh_from_db()
        batch_profile.refresh_from_db()
        self.assertEqual(result["recovered_units"], 1)
        self.assertEqual(item.status, RefreshWorkItem.Status.QUEUED)
        self.assertEqual(item.attempts, 1)
        self.assertEqual(item.lease_token, "")
        self.assertIsNone(item.lease_expires_at)
        self.assertEqual(item.error_category, "execution_interrupted")
        self.assertEqual(source_run.status, OperationalRun.Status.RUNNING)
        self.assertEqual(profile_run.status, OperationalRun.Status.RUNNING)
        self.assertIsNone(batch_profile.finished_at)

        reconcile_refresh_work.run()
        item.refresh_from_db()
        self.assertEqual(item.status, RefreshWorkItem.Status.QUEUED)
        self.assertEqual(item.attempts, 1)
        dispatch.assert_called_once_with(item.pk)

    @patch("jobs.resumable.release_refresh_lease")
    def test_exhausted_stale_unit_closes_runs_and_releases_profile_lease(self, release_lease):
        item, source_run, profile_run, batch_profile = self.make_running_item(attempts=3)

        result = reconcile_refresh_work.run()

        item.refresh_from_db()
        source_run.refresh_from_db()
        profile_run.refresh_from_db()
        batch_profile.refresh_from_db()
        self.assertEqual(result["recovered_units"], 0)
        self.assertEqual(item.status, RefreshWorkItem.Status.FAILED)
        self.assertEqual(item.error_category, "execution_interrupted")
        self.assertEqual(item.lease_token, "")
        self.assertIsNone(item.lease_expires_at)
        self.assertEqual(source_run.status, OperationalRun.Status.FAILED)
        self.assertEqual(source_run.error_category, "execution_interrupted")
        self.assertEqual(profile_run.status, OperationalRun.Status.FAILED)
        self.assertIsNotNone(batch_profile.finished_at)
        release_lease.assert_called_once_with("profile-refresh:1", batch_profile.lease_token)

    @patch("jobs.resumable.process_refresh_work_item.delay")
    def test_recent_heartbeat_and_valid_lease_preserve_active_unit(self, dispatch):
        item, source_run, _, _ = self.make_running_item(
            heartbeat_age_minutes=5,
            lease_expired=False,
        )
        item.heartbeat_at = timezone.now()
        item.save(update_fields=("heartbeat_at",))

        reconcile_refresh_work.run()

        item.refresh_from_db()
        source_run.refresh_from_db()
        self.assertEqual(item.status, RefreshWorkItem.Status.RUNNING)
        self.assertEqual(source_run.status, OperationalRun.Status.RUNNING)
        dispatch.assert_not_called()
