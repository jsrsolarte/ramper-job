from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import OperationalParameter, PeriodicRefreshState
from .parameters import PROCESSING_PAUSED_KEY, REFRESH_INTERVAL_KEY
from .scheduling import next_periodic_refresh_schedule, record_periodic_refresh_start


class PeriodicRefreshScheduleTests(TestCase):
    @override_settings(TIME_ZONE="America/Bogota")
    def test_without_a_periodic_cycle_the_schedule_is_unavailable(self):
        self.assertEqual(next_periodic_refresh_schedule(), {"status": "unavailable", "next_at": None})

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

        self.assertEqual(next_periodic_refresh_schedule(), {"status": "paused", "next_at": None})

    def test_periodic_start_timestamp_is_persisted_and_updated(self):
        first = timezone.now() - timedelta(hours=2)
        second = timezone.now()

        record_periodic_refresh_start(started_at=first)
        record_periodic_refresh_start(started_at=second)

        self.assertEqual(PeriodicRefreshState.objects.count(), 1)
        self.assertEqual(PeriodicRefreshState.objects.get(pk=1).last_started_at, second)


class ScheduleViewIntegrationTests(TestCase):
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
