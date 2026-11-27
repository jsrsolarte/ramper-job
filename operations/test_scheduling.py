from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    AutomaticSearchSchedule, OperationalParameter, OperationalRun, PeriodicRefreshState,
    RefreshBatch, RefreshWorkItem,
)
from .parameters import (
    DEFAULT_SEARCH_PAUSE_END,
    DEFAULT_SEARCH_PAUSE_START,
    PROCESSING_PAUSED_KEY,
    REFRESH_INTERVAL_KEY,
    automatic_search_schedule,
    save_automatic_search_schedule,
)
from .scheduling import (automatic_searches_paused, claim_periodic_refresh_start,
                         next_periodic_refresh_schedule, record_periodic_refresh_start)


class PeriodicRefreshScheduleTests(TestCase):
    @override_settings(TIME_ZONE="America/Bogota")
    def test_default_window_includes_start_excludes_end_and_crosses_midnight(self):
        from zoneinfo import ZoneInfo

        bogota = ZoneInfo("America/Bogota")
        self.assertFalse(automatic_searches_paused(now=timezone.make_aware(datetime(2026, 11, 12, 20, 59), bogota)))
        self.assertTrue(automatic_searches_paused(now=timezone.make_aware(datetime(2026, 11, 12, 21, 0), bogota)))
        self.assertTrue(automatic_searches_paused(now=timezone.make_aware(datetime(2026, 11, 13, 6, 59), bogota)))
        self.assertFalse(automatic_searches_paused(now=timezone.make_aware(datetime(2026, 11, 13, 7, 0), bogota)))

    def test_default_values_and_same_day_window_boundaries(self):
        from zoneinfo import ZoneInfo

        self.assertEqual(automatic_search_schedule(), {
            "enabled": True,
            "starts_at": DEFAULT_SEARCH_PAUSE_START,
            "ends_at": DEFAULT_SEARCH_PAUSE_END,
        })
        AutomaticSearchSchedule.objects.create(pk=1, enabled=True, starts_at=time(12), ends_at=time(14))
        bogota = ZoneInfo("America/Bogota")
        self.assertFalse(automatic_searches_paused(now=timezone.make_aware(datetime(2026, 11, 12, 11, 59), bogota)))
        self.assertTrue(automatic_searches_paused(now=timezone.make_aware(datetime(2026, 11, 12, 12, 0), bogota)))
        self.assertTrue(automatic_searches_paused(now=timezone.make_aware(datetime(2026, 11, 12, 13, 59), bogota)))
        self.assertFalse(automatic_searches_paused(now=timezone.make_aware(datetime(2026, 11, 12, 14, 0), bogota)))

    def test_disabled_window_never_pauses_and_equal_times_are_rejected(self):
        from datetime import time

        actor = get_user_model().objects.create_superuser("schedule-actor", password="strong-pass")
        AutomaticSearchSchedule.objects.create(pk=1, enabled=False, starts_at=time(21), ends_at=time(7))
        self.assertFalse(automatic_searches_paused())
        with self.assertRaises(ValueError):
            save_automatic_search_schedule(actor=actor, enabled=True, starts_at=time(9), ends_at=time(9))

    def test_unspecified_historical_batch_origin_defaults_to_automatic(self):
        batch = RefreshBatch.objects.create()

        self.assertEqual(batch.origin, RefreshBatch.Origin.AUTOMATIC)

    @override_settings(TIME_ZONE="America/Bogota")
    @override_settings(JOB_REFRESH_MINUTES=120)
    def test_without_a_recorded_cycle_does_not_invent_a_future_estimate(self):
        now = timezone.make_aware(datetime(2026, 11, 12, 14, 0))
        result = next_periodic_refresh_schedule(now=now)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["next_at"])
        self.assertIsNone(result["last_started_at"])

    @override_settings(TIME_ZONE="America/Bogota")
    def test_estimate_uses_current_interval_and_changes_when_interval_changes(self):
        last_started_at = timezone.make_aware(datetime(2026, 11, 12, 14, 0))
        record_periodic_refresh_start(started_at=last_started_at)
        interval = OperationalParameter.objects.create(key=REFRESH_INTERVAL_KEY, value=60)

        first = next_periodic_refresh_schedule(now=last_started_at)
        self.assertEqual(first["status"], "scheduled")
        self.assertEqual(first["next_at"], last_started_at + timedelta(minutes=60))
        self.assertFalse(first["is_overdue"])

        interval.value = 90
        interval.save(update_fields=("value",))
        second = next_periodic_refresh_schedule(now=last_started_at)
        self.assertEqual(second["next_at"], last_started_at + timedelta(minutes=90))

    def test_global_pause_hides_the_estimated_date(self):
        last_started_at = timezone.now()
        record_periodic_refresh_start(started_at=last_started_at)
        OperationalParameter.objects.create(key=PROCESSING_PAUSED_KEY, value=1)

        schedule = next_periodic_refresh_schedule()
        self.assertEqual(schedule["status"], "paused")
        self.assertIsNone(schedule["next_at"])
        self.assertEqual(schedule["last_started_at"], timezone.localtime(last_started_at))

    @override_settings(JOB_REFRESH_MINUTES=120)
    def test_estimate_that_lands_inside_future_quiet_window_moves_to_window_end(self):
        from zoneinfo import ZoneInfo

        now = timezone.make_aware(datetime(2026, 11, 12, 20, 0), ZoneInfo("America/Bogota"))
        record_periodic_refresh_start(started_at=now)
        schedule = next_periodic_refresh_schedule(now=now)
        self.assertEqual(schedule["next_at"], timezone.make_aware(
            datetime(2026, 11, 13, 7, 0), ZoneInfo("America/Bogota"),
        ))

    @override_settings(JOB_REFRESH_MINUTES=15)
    def test_overdue_estimate_during_quiet_window_moves_to_future_window_end(self):
        from zoneinfo import ZoneInfo

        bogota = ZoneInfo("America/Bogota")
        last_started = timezone.make_aware(datetime(2026, 11, 12, 20, 45), bogota)
        now = timezone.make_aware(datetime(2026, 11, 12, 22, 30), bogota)
        record_periodic_refresh_start(started_at=last_started)

        schedule = next_periodic_refresh_schedule(now=now)

        self.assertEqual(schedule["next_at"], timezone.make_aware(datetime(2026, 11, 13, 7, 0), bogota))
        self.assertFalse(schedule["is_overdue"])
        self.assertTrue(schedule["quiet_window"])

    @override_settings(JOB_REFRESH_MINUTES=60)
    def test_overdue_cycle_keeps_the_original_estimate_and_marks_it_overdue(self):
        from zoneinfo import ZoneInfo

        bogota = ZoneInfo("America/Bogota")
        last_started = timezone.make_aware(datetime(2026, 11, 12, 16, 34), bogota)
        now = timezone.make_aware(datetime(2026, 11, 12, 18, 0), bogota)
        record_periodic_refresh_start(started_at=last_started)

        schedule = next_periodic_refresh_schedule(now=now)

        self.assertEqual(schedule["status"], "overdue")
        self.assertEqual(schedule["next_at"], last_started + timedelta(minutes=60))
        self.assertEqual(schedule["last_started_at"], last_started)
        self.assertTrue(schedule["is_overdue"])

        cycle_started = now + timedelta(minutes=2)
        self.assertEqual(claim_periodic_refresh_start(started_at=cycle_started), cycle_started)
        recovered = next_periodic_refresh_schedule(now=cycle_started + timedelta(minutes=1))
        self.assertEqual(recovered["status"], "scheduled")
        self.assertEqual(recovered["last_started_at"], cycle_started)
        self.assertEqual(recovered["next_at"], cycle_started + timedelta(minutes=60))

    def test_work_state_requires_a_live_lease_and_recent_heartbeat(self):
        now = timezone.now()
        batch = RefreshBatch.objects.create(status=RefreshBatch.Status.RUNNING, heartbeat_at=now)
        source_run = OperationalRun.objects.create(
            kind=OperationalRun.Kind.INGESTION,
            operation="source_query",
            started_at=now,
        )
        item = RefreshWorkItem.objects.create(
            batch=batch,
            source_run=source_run,
            source="elempleo_co",
            identity="safe-test-identity",
            status=RefreshWorkItem.Status.RUNNING,
            heartbeat_at=now,
            lease_expires_at=now + timedelta(minutes=5),
        )

        self.assertEqual(next_periodic_refresh_schedule(now=now)["work_state"], "active")

        item.lease_expires_at = now - timedelta(seconds=1)
        item.heartbeat_at = now - timedelta(minutes=20)
        item.save(update_fields=("lease_expires_at", "heartbeat_at"))
        batch.heartbeat_at = now - timedelta(minutes=20)
        batch.save(update_fields=("heartbeat_at",))
        self.assertEqual(next_periodic_refresh_schedule(now=now)["work_state"], "uncertain")

        item.status = RefreshWorkItem.Status.QUEUED
        item.save(update_fields=("status",))
        batch.status = RefreshBatch.Status.QUEUED
        batch.save(update_fields=("status",))
        self.assertEqual(next_periodic_refresh_schedule(now=now)["work_state"], "queued")

        item.status = RefreshWorkItem.Status.RUNNING
        item.heartbeat_at = now
        item.lease_expires_at = now + timedelta(minutes=5)
        item.save(update_fields=("status", "heartbeat_at", "lease_expires_at"))
        batch.status = RefreshBatch.Status.RUNNING
        batch.heartbeat_at = now
        batch.save(update_fields=("status", "heartbeat_at"))
        OperationalParameter.objects.create(key=PROCESSING_PAUSED_KEY, value=1)
        paused = next_periodic_refresh_schedule(now=now)
        self.assertEqual(paused["status"], "paused")
        self.assertEqual(paused["work_state"], "active")

    def test_periodic_start_timestamp_is_persisted_and_updated(self):
        first = timezone.now() - timedelta(hours=2)
        second = timezone.now()

        record_periodic_refresh_start(started_at=first)
        record_periodic_refresh_start(started_at=second)

        self.assertEqual(PeriodicRefreshState.objects.count(), 1)
        self.assertEqual(PeriodicRefreshState.objects.get(pk=1).last_started_at, second)

    def test_only_one_due_cycle_can_be_claimed_within_the_interval(self):
        first = timezone.now() - timedelta(hours=3)
        due = timezone.now()
        record_periodic_refresh_start(started_at=first)
        self.assertEqual(claim_periodic_refresh_start(started_at=due), due)
        self.assertIsNone(claim_periodic_refresh_start(started_at=due + timedelta(minutes=1)))


class ScheduleViewIntegrationTests(TestCase):
    def test_schedule_is_auditable_admin_only_and_rejects_equal_times(self):
        from .models import AutomaticSearchScheduleChange

        admin = get_user_model().objects.create_superuser("schedule-admin-edit", password="strong-pass")
        applicant = get_user_model().objects.create_user("schedule-applicant-edit", password="strong-pass")
        url = reverse("operations:parameters")
        self.client.force_login(applicant)
        self.assertEqual(self.client.post(url, {
            "parameter": "automatic_search_schedule", "action": "save",
            "pause_start": "22:00", "pause_end": "06:00", "pause_enabled": "on",
        }).status_code, 403)
        self.client.force_login(admin)
        AutomaticSearchSchedule.objects.create(pk=1, enabled=True, starts_at=time(21), ends_at=time(7))
        invalid = self.client.post(url, {
            "parameter": "automatic_search_schedule", "action": "save",
            "pause_start": "22:00", "pause_end": "22:00", "pause_enabled": "on",
        })
        self.assertEqual(invalid.status_code, 400)
        self.assertFalse(AutomaticSearchScheduleChange.objects.exists())
        schedule = AutomaticSearchSchedule.objects.get(pk=1)
        self.assertEqual((schedule.enabled, schedule.starts_at, schedule.ends_at), (True, time(21), time(7)))
        response = self.client.post(url, {
            "parameter": "automatic_search_schedule", "action": "save",
            "pause_start": "22:00", "pause_end": "06:00", "pause_enabled": "on",
        })
        self.assertEqual(response.status_code, 302)
        change = AutomaticSearchScheduleChange.objects.get()
        self.assertEqual(change.actor, admin)
        self.assertEqual((change.new_starts_at.hour, change.new_ends_at.hour), (22, 6))

    def test_applicant_and_admin_views_share_the_estimate_after_interval_change(self):
        applicant = get_user_model().objects.create_user("schedule-applicant", password="strong-pass")
        admin = get_user_model().objects.create_superuser("schedule-admin", password="strong-pass")
        last_started_at = timezone.make_aware(datetime(2026, 11, 12, 14, 0))
        record_periodic_refresh_start(started_at=last_started_at)
        interval = OperationalParameter.objects.create(key=REFRESH_INTERVAL_KEY, value=60)
        applicant_client = self.client
        admin_client = type(self.client)()
        applicant_client.force_login(applicant)
        admin_client.force_login(admin)

        first_dashboard = applicant_client.get(reverse("dashboard:home"))
        first_admin = admin_client.get(reverse("operations:admin_center"))
        self.assertEqual(first_dashboard.context["automatic_refresh_schedule"], first_admin.context["automatic_refresh_schedule"])
        self.assertEqual(first_dashboard.context["automatic_refresh_schedule"]["next_at"], last_started_at + timedelta(minutes=60))

        interval.value = 90
        interval.save(update_fields=("value",))
        changed_dashboard = applicant_client.get(reverse("dashboard:home"))
        changed_admin = admin_client.get(reverse("operations:admin_center"))
        schedule = changed_dashboard.context["automatic_refresh_schedule"]
        self.assertEqual(schedule, changed_admin.context["automatic_refresh_schedule"])
        self.assertEqual(schedule["next_at"], last_started_at + timedelta(minutes=90))
        self.assertContains(changed_dashboard, schedule["next_at"].strftime("%H:%M"))
        self.assertContains(changed_admin, schedule["next_at"].strftime("%H:%M"))

    def test_schedule_status_endpoint_is_authenticated_and_hides_last_start_from_applicants(self):
        from datetime import datetime

        applicant = get_user_model().objects.create_user("schedule-status-applicant", password="strong-pass")
        admin = get_user_model().objects.create_superuser("schedule-status-admin", password="strong-pass")
        last_started = timezone.make_aware(datetime(2026, 11, 12, 14, 0))
        record_periodic_refresh_start(started_at=last_started)
        applicant_client = type(self.client)()
        admin_client = type(self.client)()

        self.assertEqual(applicant_client.get(reverse("operations:schedule_status")).status_code, 302)
        applicant_client.force_login(applicant)
        applicant_response = applicant_client.get(reverse("operations:schedule_status"))
        self.assertEqual(applicant_response.status_code, 200)
        self.assertNotIn("last_started_at", applicant_response.json())
        self.assertEqual(applicant_client.get(reverse("operations:admin_schedule_status")).status_code, 403)

        admin_client.force_login(admin)
        admin_response = admin_client.get(reverse("operations:admin_schedule_status"))
        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(admin_response.json()["last_started_at"], last_started.isoformat())
