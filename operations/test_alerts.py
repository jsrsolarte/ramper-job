from datetime import timedelta
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.db import close_old_connections
from django.utils import timezone

from operations.alerts import evaluate_operational_alerts, operational_alert_health
from operations.models import (
    OperationalAlertPushAttempt,
    OperationalAlertState,
    OperationalAlertSubscription,
    OperationalIncident,
    OperationalRun,
    RefreshBatch,
    RefreshBatchProfile,
    RefreshWorkItem,
    RefreshWorkProfile,
)
from operations.alerts import send_pending_operational_alerts
from operations.alerts import _periodic_cycle_findings, _no_progress_findings
from profiles.models import Profile


class OperationalAlertEvaluationTests(TestCase):
    def setUp(self):
        self.now = timezone.now().replace(second=0, microsecond=0)
        OperationalAlertState.objects.create(pk=1, activated_at=self.now - timedelta(hours=1))

    def add_failure(self, *, minutes_ago=5, category="omniroute.timeout", source="magneto_co"):
        return OperationalRun.objects.create(
            kind=OperationalRun.Kind.INGESTION,
            operation="source_refresh",
            source=source,
            status=OperationalRun.Status.FAILED,
            error_category=category,
            started_at=self.now - timedelta(minutes=minutes_ago),
        )

    @patch("operations.alerts.send_pending_operational_alerts", return_value={"attempted": 0})
    @patch("operations.alerts._eligible_profiles")
    @patch("operations.alerts.automatic_searches_paused", return_value=False)
    @patch("operations.alerts.processing_is_paused", return_value=False)
    def test_three_distinct_failures_open_one_safe_grouped_incident(self, *_mocks):
        for _ in range(3):
            self.add_failure()
        result = evaluate_operational_alerts(now=self.now)
        self.assertEqual(result["status"], "ok")
        incident = OperationalIncident.objects.get()
        self.assertEqual(incident.count, 3)
        self.assertEqual(incident.component, "magneto_co")
        self.assertEqual(incident.category, "omniroute.timeout")

    @patch("operations.alerts.send_pending_operational_alerts", return_value={"attempted": 0})
    @patch("operations.alerts._eligible_profiles")
    @patch("operations.alerts.automatic_searches_paused", return_value=False)
    @patch("operations.alerts.processing_is_paused", return_value=False)
    def test_single_failure_does_not_open_incident(self, *_mocks):
        self.add_failure()
        evaluate_operational_alerts(now=self.now)
        self.assertFalse(OperationalIncident.objects.exists())

    @patch("operations.alerts.send_pending_operational_alerts", return_value={"attempted": 0})
    @patch("operations.alerts._eligible_profiles")
    @patch("operations.alerts.automatic_searches_paused", return_value=False)
    @patch("operations.alerts.processing_is_paused", return_value=False)
    def test_incident_recovers_only_after_two_clear_checks(self, *_mocks):
        for _ in range(3):
            self.add_failure()
        evaluate_operational_alerts(now=self.now)
        incident = OperationalIncident.objects.get()
        OperationalRun.objects.update(status=OperationalRun.Status.SUCCEEDED)
        evaluate_operational_alerts(now=self.now + timedelta(minutes=5))
        incident.refresh_from_db()
        self.assertEqual(incident.status, OperationalIncident.Status.OPEN)
        evaluate_operational_alerts(now=self.now + timedelta(minutes=10))
        incident.refresh_from_db()
        self.assertEqual(incident.status, OperationalIncident.Status.RECOVERED)

    @patch("operations.alerts.send_pending_operational_alerts", return_value={"attempted": 0})
    @patch("operations.alerts._eligible_profiles")
    @patch("operations.alerts.automatic_searches_paused", return_value=False)
    @patch("operations.alerts.processing_is_paused", return_value=False)
    def test_recurrence_after_recovery_opens_a_new_episode(self, *_mocks):
        runs = [self.add_failure() for _ in range(3)]
        evaluate_operational_alerts(now=self.now)
        first = OperationalIncident.objects.get()
        OperationalRun.objects.update(status=OperationalRun.Status.SUCCEEDED)
        evaluate_operational_alerts(now=self.now + timedelta(minutes=5))
        evaluate_operational_alerts(now=self.now + timedelta(minutes=10))
        for run in runs:
            run.status = OperationalRun.Status.FAILED
            run.save(update_fields=("status",))
        evaluate_operational_alerts(now=self.now + timedelta(minutes=15))
        self.assertEqual(OperationalIncident.objects.count(), 2)
        first.refresh_from_db()
        self.assertEqual(first.status, OperationalIncident.Status.RECOVERED)
        self.assertEqual(OperationalIncident.objects.get(status=OperationalIncident.Status.OPEN).count, 3)

    @patch("operations.alerts.send_pending_operational_alerts", return_value={"attempted": 0})
    @patch("operations.alerts._failure_findings", side_effect=RuntimeError("private exception text"))
    def test_failed_evaluation_reports_unknown_without_resolving_incident(self, _failure, _send):
        incident = OperationalIncident.objects.create(
            kind=OperationalIncident.Kind.RECURRING_FAILURE,
            component="magneto_co", category="otro_error",
            first_observed_at=self.now - timedelta(minutes=40),
            last_observed_at=self.now - timedelta(minutes=1),
        )
        result = evaluate_operational_alerts(now=self.now)
        incident.refresh_from_db()
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(incident.status, OperationalIncident.Status.OPEN)
        self.assertEqual(operational_alert_health(now=self.now)["status"], "unknown")

    def test_periodic_cycle_alert_respects_overdue_margin_and_global_pause(self):
        from operations.models import OperationalIncident
        from operations import alerts
        schedule = {"status": "overdue", "next_at": self.now - timedelta(minutes=31)}
        with patch.object(alerts, "next_periodic_refresh_schedule", return_value=schedule):
            finding = _periodic_cycle_findings(
                now=self.now, activated_at=self.now - timedelta(hours=1),
                profiles_available=True, globally_paused=False,
            )
            paused = _periodic_cycle_findings(
                now=self.now, activated_at=self.now - timedelta(hours=1),
                profiles_available=True, globally_paused=True,
            )
            no_profiles = _periodic_cycle_findings(
                now=self.now, activated_at=self.now - timedelta(hours=1),
                profiles_available=False, globally_paused=False,
            )
        with patch.object(alerts, "next_periodic_refresh_schedule", return_value={
            "status": "overdue", "next_at": self.now - timedelta(minutes=20),
        }):
            below_margin = _periodic_cycle_findings(
                now=self.now, activated_at=self.now - timedelta(hours=1),
                profiles_available=True, globally_paused=False,
            )
        self.assertIn((OperationalIncident.Kind.PERIODIC_OVERDUE, "planificador", "ciclo_no_iniciado"), finding)
        self.assertEqual(paused, {})
        self.assertEqual(no_profiles, {})
        self.assertEqual(below_margin, {})
        with patch.object(alerts, "next_periodic_refresh_schedule", return_value={
            "status": "scheduled", "next_at": self.now + timedelta(minutes=5),
        }):
            self.assertEqual(_periodic_cycle_findings(
                now=self.now, activated_at=self.now - timedelta(hours=1),
                profiles_available=True, globally_paused=False,
            ), {})

    def test_no_progress_signal_does_not_alert_when_global_pause_is_active(self):
        result = _no_progress_findings(
            now=self.now, activated_at=self.now - timedelta(hours=1),
            globally_paused=True, quiet_window=False,
        )
        self.assertEqual(result, {})

    def test_no_progress_search_respects_profile_pause_quiet_window_and_lease(self):
        user = get_user_model().objects.create_user(username="search-profile", password="test-pass")
        profile = Profile.objects.create(owner=user, revision_number=1)
        run = OperationalRun.objects.create(
            kind=OperationalRun.Kind.INGESTION, operation="refresh", source="magneto_co",
        )
        batch = RefreshBatch.objects.create(origin=RefreshBatch.Origin.AUTOMATIC)
        batch_profile = RefreshBatchProfile.objects.create(
            batch=batch, profile=profile, profile_run=run, lease_token="synthetic",
        )
        item = RefreshWorkItem.objects.create(
            batch=batch, source_run=run, source="magneto_co", identity="synthetic-item",
            status=RefreshWorkItem.Status.RUNNING,
            heartbeat_at=self.now - timedelta(minutes=40),
            lease_expires_at=self.now + timedelta(minutes=5),
        )
        RefreshWorkProfile.objects.create(
            work_item=item, batch_profile=batch_profile, revision_id=profile.revision_number,
        )
        findings = _no_progress_findings(
            now=self.now, activated_at=self.now - timedelta(hours=1),
            globally_paused=False, quiet_window=False,
        )
        self.assertEqual(findings, {})
        item.lease_expires_at = self.now - timedelta(minutes=1)
        item.save(update_fields=("lease_expires_at",))
        findings = _no_progress_findings(
            now=self.now, activated_at=self.now - timedelta(hours=1),
            globally_paused=False, quiet_window=False,
        )
        self.assertIn((OperationalIncident.Kind.NO_PROGRESS, "magneto_co", "sin_progreso"), findings)
        self.assertEqual(_no_progress_findings(
            now=self.now, activated_at=self.now - timedelta(hours=1),
            globally_paused=False, quiet_window=True,
        ), {})
        profile.search_enabled = False
        profile.save(update_fields=("search_enabled", "updated_at"))
        self.assertEqual(_no_progress_findings(
            now=self.now, activated_at=self.now - timedelta(hours=1),
            globally_paused=False, quiet_window=False,
        ), {})


class OperationalAlertAdminTests(TestCase):
    def test_non_admin_cannot_access_center_or_acknowledge_incident(self):
        user = get_user_model().objects.create_user(username="applicant", password="test-pass")
        incident = OperationalIncident.objects.create(
            kind=OperationalIncident.Kind.NO_PROGRESS,
            component="analisis", category="sin_progreso",
            first_observed_at=timezone.now(), last_observed_at=timezone.now(),
        )
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("operations:admin_center")).status_code, 403)
        self.assertEqual(self.client.post(
            reverse("operations:acknowledge_operational_incident", args=[incident.pk]),
        ).status_code, 403)
        incident.refresh_from_db()
        self.assertEqual(incident.status, OperationalIncident.Status.OPEN)

    def test_admin_can_acknowledge_without_resolving_incident(self):
        admin = get_user_model().objects.create_superuser(username="ops", email="ops@example.test", password="test-pass")
        incident = OperationalIncident.objects.create(
            kind=OperationalIncident.Kind.NO_PROGRESS,
            component="analisis", category="sin_progreso",
            first_observed_at=timezone.now(), last_observed_at=timezone.now(),
        )
        self.client.force_login(admin)
        response = self.client.post(reverse("operations:acknowledge_operational_incident", args=[incident.pk]))
        incident.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(incident.status, OperationalIncident.Status.ACKNOWLEDGED)
        self.assertEqual(incident.acknowledged_by, admin)

    def test_admin_center_shows_only_safe_aggregated_incident_data(self):
        admin = get_user_model().objects.create_superuser(
            username="safe-admin", email="safe-admin@example.test", password="test-pass",
        )
        OperationalIncident.objects.create(
            kind=OperationalIncident.Kind.RECURRING_FAILURE,
            component="magneto_co", category="omniroute.timeout", count=3,
            first_observed_at=timezone.now(), last_observed_at=timezone.now(),
        )
        OperationalIncident.objects.create(
            kind=OperationalIncident.Kind.NO_PROGRESS,
            component="analisis", category="sin_progreso", status=OperationalIncident.Status.RECOVERED,
            first_observed_at=timezone.now(), last_observed_at=timezone.now(), recovered_at=timezone.now(),
        )
        self.client.force_login(admin)
        response = self.client.get(reverse("operations:admin_center"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "magneto_co")
        self.assertContains(response, "omniroute.timeout")
        self.assertContains(response, "desconocido")
        self.assertContains(response, "Incidentes recuperados")

    def test_logout_unlinks_admin_alert_subscription_and_worker_uses_generic_text(self):
        admin = get_user_model().objects.create_superuser(
            username="logout-admin", email="logout@example.test", password="test-pass",
        )
        from operations.alerts import push_endpoint_digest
        endpoint = "https://push.example.test/logout-device"
        subscription = OperationalAlertSubscription(
            user=admin, endpoint_digest=push_endpoint_digest(endpoint), active=True,
        )
        subscription.endpoint = endpoint
        subscription.p256dh_key = "public-key"
        subscription.auth_key = "auth-key"
        subscription.save()
        self.client.force_login(admin)
        self.client.post(reverse("logout"), {"push_endpoint": endpoint})
        self.assertFalse(OperationalAlertSubscription.objects.filter(pk=subscription.pk).exists())
        worker = self.client.get(reverse("push_service_worker"))
        self.assertContains(worker, "Hay una alerta operativa.")
        self.assertContains(worker, "/admin/operaciones/")

    def test_push_consent_is_separate_encrypted_and_can_be_disabled(self):
        from operations.alerts import push_endpoint_digest
        admin = get_user_model().objects.create_superuser(
            username="push-settings", email="push-settings@example.test", password="test-pass",
        )
        self.client.force_login(admin)
        endpoint = "https://push.example.test/admin-device"
        payload = {
            "enabled": True,
            "subscription": {"endpoint": endpoint, "keys": {"p256dh": "public-key", "auth": "auth-key"}},
        }
        response = self.client.post(
            reverse("operations:operational_alert_push_subscription"),
            data=json.dumps(payload), content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        row = OperationalAlertSubscription.objects.get(endpoint_digest=push_endpoint_digest(endpoint))
        self.assertTrue(row.active)
        self.assertNotIn(endpoint, row.endpoint_ciphertext)
        response = self.client.post(
            reverse("operations:operational_alert_push_subscription"),
            data=json.dumps({"enabled": False, "subscription": {"endpoint": endpoint}}),
            content_type="application/json",
        )
        row.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(row.active)


class OperationalAlertPushTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="push-admin", email="push@example.test", password="test-pass",
        )
        self.endpoint = "https://push.example.test/subscription/device-1"
        from operations.alerts import push_endpoint_digest
        self.subscription = OperationalAlertSubscription(
            user=self.admin, endpoint_digest=push_endpoint_digest(self.endpoint), active=True,
            last_notified_incident_id=0,
        )
        self.subscription.endpoint = self.endpoint
        self.subscription.p256dh_key = "synthetic-public-key"
        self.subscription.auth_key = "synthetic-auth-key"
        self.subscription.save()
        self.incident = OperationalIncident.objects.create(
            kind=OperationalIncident.Kind.NO_PROGRESS,
            component="analisis", category="sin_progreso",
            first_observed_at=timezone.now(), last_observed_at=timezone.now(),
        )

    def test_push_is_generic_and_limited_to_one_per_device_per_six_hours(self):
        sent = []
        now = timezone.now()
        result = send_pending_operational_alerts(now=now, sender=lambda info: sent.append(info))
        self.assertEqual(result["attempted"], 1)
        self.assertEqual(sent[0]["endpoint"], self.endpoint)
        self.assertEqual(OperationalAlertPushAttempt.objects.get().status, OperationalAlertPushAttempt.Status.SENT)
        send_pending_operational_alerts(now=now + timedelta(hours=1), sender=lambda info: sent.append(info))
        self.assertEqual(len(sent), 1)

    def test_recovered_incident_is_not_sent_after_cooldown(self):
        self.incident.status = OperationalIncident.Status.RECOVERED
        self.incident.recovered_at = timezone.now()
        self.incident.save(update_fields=("status", "recovered_at", "updated_at"))
        sent = []
        result = send_pending_operational_alerts(sender=lambda info: sent.append(info))
        self.assertEqual(result["attempted"], 0)
        self.assertEqual(sent, [])
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.last_notified_incident_id, self.incident.pk)

    def test_ambiguous_failure_is_reserved_and_never_retried(self):
        sent = []
        def uncertain(_info):
            sent.append(True)
            raise TimeoutError("sensitive response must not be logged")
        send_pending_operational_alerts(sender=uncertain)
        attempt = OperationalAlertPushAttempt.objects.get()
        self.assertEqual(attempt.status, OperationalAlertPushAttempt.Status.FAILED)
        self.assertEqual(attempt.failure_category, "push_error")
        send_pending_operational_alerts(now=timezone.now() + timedelta(hours=7), sender=uncertain)
        self.assertEqual(len(sent), 1)

    def test_expired_endpoint_is_deactivated(self):
        class ExpiredEndpoint(Exception):
            status_code = 410
        send_pending_operational_alerts(sender=lambda _info: (_ for _ in ()).throw(ExpiredEndpoint()))
        self.subscription.refresh_from_db()
        self.assertFalse(self.subscription.active)


class OperationalAlertPushConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def test_concurrent_evaluators_reserve_only_one_push_per_device(self):
        admin = get_user_model().objects.create_superuser(
            username="concurrent-admin", email="concurrent@example.test", password="test-pass",
        )
        endpoint = "https://push.example.test/concurrent-device"
        from operations.alerts import push_endpoint_digest
        subscription = OperationalAlertSubscription(
            user=admin, endpoint_digest=push_endpoint_digest(endpoint), active=True,
        )
        subscription.endpoint = endpoint
        subscription.p256dh_key = "public-key"
        subscription.auth_key = "auth-key"
        subscription.save()
        OperationalIncident.objects.create(
            kind=OperationalIncident.Kind.NO_PROGRESS,
            component="analisis", category="sin_progreso",
            first_observed_at=timezone.now(), last_observed_at=timezone.now(),
        )
        ready = Barrier(2)
        sent = []

        def evaluate():
            close_old_connections()
            ready.wait(timeout=5)
            result = send_pending_operational_alerts(sender=lambda info: sent.append(info["endpoint"]))
            close_old_connections()
            return result

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _index: evaluate(), range(2)))
        self.assertEqual(sum(result["attempted"] for result in results), 1)
        self.assertEqual(sent, [endpoint])
        self.assertEqual(OperationalAlertPushAttempt.objects.count(), 1)

