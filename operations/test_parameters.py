from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import OperationalParameter, OperationalParameterChange
from .parameters import (
    AUTO_DISCARD_DAYS_KEY,
    DEFAULT_AUTO_DISCARD_DAYS,
    DEFAULT_FOLLOW_UP_ARCHIVE_DAYS,
    FOLLOW_UP_ARCHIVE_DAYS_KEY,
    MAX_REFRESH_MINUTES,
    MAX_RETENTION_DAYS,
    MIN_REFRESH_MINUTES,
    MIN_RETENTION_DAYS,
    REFRESH_INTERVAL_KEY,
    current_auto_discard_days,
    current_follow_up_archive_days,
    current_refresh_interval_minutes,
    initial_refresh_interval_minutes,
)
from .schedules import DatabaseRefreshInterval


class OperationalParameterServiceTests(TestCase):
    @override_settings(JOB_REFRESH_MINUTES=90)
    def test_environment_value_is_initial_and_database_value_takes_precedence(self):
        self.assertEqual(initial_refresh_interval_minutes(), 90)
        self.assertEqual(current_refresh_interval_minutes(), 90)
        OperationalParameter.objects.create(key=REFRESH_INTERVAL_KEY, value=75)
        self.assertEqual(current_refresh_interval_minutes(), 75)

    @override_settings(JOB_REFRESH_MINUTES=10)
    def test_invalid_environment_value_falls_back_to_120_minutes(self):
        self.assertEqual(initial_refresh_interval_minutes(), 120)

    @override_settings(JOB_REFRESH_MINUTES=90)
    def test_beat_schedule_reads_database_changes_without_restarting(self):
        periodic = DatabaseRefreshInterval()
        periodic.is_due(timezone.now() - timedelta(minutes=100))
        self.assertEqual(periodic.run_every, timedelta(minutes=90))

        OperationalParameter.objects.create(key=REFRESH_INTERVAL_KEY, value=45)
        periodic.is_due(timezone.now() - timedelta(minutes=100))
        self.assertEqual(periodic.run_every, timedelta(minutes=45))


class OperationalParameterViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser("operator", password="strong-pass")
        self.applicant = user_model.objects.create_user("applicant", password="strong-pass")
        self.url = reverse("operations:parameters")

    @override_settings(JOB_REFRESH_MINUTES=120)
    def test_staff_can_consult_current_value_and_visible_limits(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "120 minutos")
        self.assertContains(response, "15 a 1440 minutos")

    @override_settings(JOB_REFRESH_MINUTES=120)
    def test_staff_can_change_interval_and_audit_actor_and_old_new_values(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(self.url, {
            "parameter": REFRESH_INTERVAL_KEY,
            "action": "save",
            "value": "60",
        })

        self.assertRedirects(response, self.url)
        self.assertEqual(current_refresh_interval_minutes(), 60)
        change = OperationalParameterChange.objects.get()
        self.assertEqual(change.changed_by, self.admin_user)
        self.assertEqual(change.previous_value, 120)
        self.assertEqual(change.new_value, 60)

    @patch("jobs.tasks.refresh_sources.delay")
    def test_save_does_not_trigger_a_manual_refresh(self, refresh_sources):
        self.client.force_login(self.admin_user)
        response = self.client.post(self.url, {
            "parameter": REFRESH_INTERVAL_KEY,
            "action": "save",
            "value": "60",
        })

        self.assertEqual(response.status_code, 302)
        refresh_sources.assert_not_called()
        self.assertEqual(OperationalParameterChange.objects.count(), 1)

    def test_invalid_values_and_unknown_keys_are_rejected(self):
        self.client.force_login(self.admin_user)
        below_minimum = self.client.post(self.url, {
            "parameter": REFRESH_INTERVAL_KEY, "action": "save", "value": str(MIN_REFRESH_MINUTES - 1),
        })
        above_maximum = self.client.post(self.url, {
            "parameter": REFRESH_INTERVAL_KEY, "action": "save", "value": str(MAX_REFRESH_MINUTES + 1),
        })
        arbitrary_parameter = self.client.post(self.url, {
            "parameter": "OMNIROUTE_API_KEY", "action": "save", "value": "secret",
        })
        extra_configuration = self.client.post(self.url, {
            "parameter": REFRESH_INTERVAL_KEY, "action": "save", "value": "60", "secret": "x",
        })

        self.assertEqual([below_minimum.status_code, above_maximum.status_code], [400, 400])
        self.assertEqual(arbitrary_parameter.status_code, 400)
        self.assertEqual(extra_configuration.status_code, 400)
        self.assertFalse(OperationalParameter.objects.exists())
        self.assertFalse(OperationalParameterChange.objects.exists())

    @override_settings(JOB_REFRESH_MINUTES=120)
    def test_reset_restores_initial_value_and_audits_both_changes(self):
        self.client.force_login(self.admin_user)
        self.client.post(self.url, {"parameter": REFRESH_INTERVAL_KEY, "action": "save", "value": "60"})

        response = self.client.post(self.url, {"parameter": REFRESH_INTERVAL_KEY, "action": "reset"})

        self.assertRedirects(response, self.url)
        self.assertEqual(current_refresh_interval_minutes(), 120)
        self.assertFalse(OperationalParameter.objects.exists())
        self.assertEqual(list(OperationalParameterChange.objects.values_list(
            "previous_value", "new_value",
        )), [(60, 120), (120, 60)])

    def test_applicant_cannot_view_or_change_operational_parameters(self):
        self.client.force_login(self.applicant)

        get_response = self.client.get(self.url)
        post_response = self.client.post(self.url, {
            "parameter": REFRESH_INTERVAL_KEY, "action": "save", "value": "60",
        })

        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(post_response.status_code, 403)
        self.assertFalse(OperationalParameter.objects.exists())

    def test_retention_parameters_have_global_defaults_and_are_shown_separately(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(current_auto_discard_days(), DEFAULT_AUTO_DISCARD_DAYS)
        self.assertEqual(current_follow_up_archive_days(), DEFAULT_FOLLOW_UP_ARCHIVE_DAYS)
        self.assertContains(response, "7 días")
        self.assertContains(response, "30 días")
        self.assertContains(response, 'value="auto_discard_days"')
        self.assertContains(response, 'value="follow_up_archive_days"')

    def test_retention_parameters_are_saved_and_audited_separately(self):
        self.client.force_login(self.admin_user)

        discard_response = self.client.post(self.url, {
            "parameter": AUTO_DISCARD_DAYS_KEY, "action": "save", "value": "9",
        })
        archive_response = self.client.post(self.url, {
            "parameter": FOLLOW_UP_ARCHIVE_DAYS_KEY, "action": "save", "value": "45",
        })

        self.assertEqual(discard_response.status_code, 302)
        self.assertEqual(archive_response.status_code, 302)
        self.assertEqual(current_auto_discard_days(), 9)
        self.assertEqual(current_follow_up_archive_days(), 45)
        self.assertEqual(
            list(OperationalParameterChange.objects.order_by("key").values_list(
                "key", "previous_value", "new_value", "changed_by_id",
            )),
            [
                (AUTO_DISCARD_DAYS_KEY, DEFAULT_AUTO_DISCARD_DAYS, 9, self.admin_user.pk),
                (FOLLOW_UP_ARCHIVE_DAYS_KEY, DEFAULT_FOLLOW_UP_ARCHIVE_DAYS, 45, self.admin_user.pk),
            ],
        )

    def test_retention_values_outside_one_to_365_are_rejected_without_changes(self):
        self.client.force_login(self.admin_user)
        self.client.post(self.url, {
            "parameter": AUTO_DISCARD_DAYS_KEY, "action": "save", "value": "12",
        })

        for value in ("0", str(MIN_RETENTION_DAYS - 1), str(MAX_RETENTION_DAYS + 1), "1.5", ""):
            with self.subTest(value=value):
                response = self.client.post(self.url, {
                    "parameter": AUTO_DISCARD_DAYS_KEY, "action": "save", "value": value,
                })
                self.assertEqual(response.status_code, 400)
                self.assertEqual(current_auto_discard_days(), 12)
        self.assertEqual(
            list(OperationalParameterChange.objects.values_list("previous_value", "new_value")),
            [(DEFAULT_AUTO_DISCARD_DAYS, 12)],
        )

    @patch("dashboard.tasks.discard_stale_recommendations.delay")
    @patch("dashboard.tasks.archive_inactive_follow_ups.delay")
    def test_saving_retention_value_does_not_enqueue_daily_tasks(self, archive_task, discard_task):
        self.client.force_login(self.admin_user)

        response = self.client.post(self.url, {
            "parameter": AUTO_DISCARD_DAYS_KEY, "action": "save", "value": "14",
        })

        self.assertEqual(response.status_code, 302)
        archive_task.assert_not_called()
        discard_task.assert_not_called()
