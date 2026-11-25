from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import hashlib
import json
from threading import Barrier
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connections
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from dashboard.models import PushDailyAttempt, PushSubscription, RecommendationEvent, VacancyFollowUp
from dashboard.push import _send_generic_push, send_daily_recommendation_summaries
from dashboard.services import (
    mark_recommendations_reviewed,
    new_recommendation_summary,
    register_recommendation_event,
)
from jobs.models import Vacancy
from matching.models import MatchingConfig, PROMPT_VERSION, VacancyAnalysis
from profiles.models import GuidedTourProgress, Profile, ProfileRevision


class RecommendationEventRegistrationTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = get_user_model().objects.create_user("recommendation-user", password="test-password")
        self.profile = Profile.objects.create(
            owner=self.user,
            locations=["Bogotá"],
            revision_number=1,
            recommendation_tracking_started_at=timezone.now() - timedelta(minutes=5),
        )
        self.revision = ProfileRevision.objects.create(
            profile=self.profile,
            version=1,
            locations=["Bogotá"],
        )
        self.config = MatchingConfig.objects.create(
            version=1,
            rubric_version=3,
            prompt_version=PROMPT_VERSION,
            analysis_prompt="Evalúa la vacante",
            organization_prompt="Organiza la vacante",
        )
        self.vacancy = self.make_vacancy("https://jobs.example.test/recommendation-1")
        self.analysis = self.make_analysis(self.profile, self.vacancy)

    @staticmethod
    def make_vacancy(url):
        return Vacancy.objects.create(
            source="test-source",
            title="Analista de datos",
            location="Bogotá",
            original_url=url,
            raw_data={"details": {"city": "Bogotá", "modality": "presencial"}},
        )

    def make_analysis(self, profile, vacancy, *, completed_at=None):
        return VacancyAnalysis.objects.create(
            profile=profile,
            profile_revision=profile.revisions.get(version=profile.revision_number),
            vacancy=vacancy,
            matching_config=self.config,
            status=VacancyAnalysis.Status.COMPLETED,
            score="8.0",
            score_breakdown={"skills": {"score": 2.0, "status": "cumple", "evidence": "SQL"}},
            completed_at=completed_at or timezone.now(),
        )

    def test_records_only_first_visible_entry_and_does_not_duplicate_reanalysis(self):
        first, created = register_recommendation_event(
            self.profile, self.vacancy, source_analysis=self.analysis
        )
        repeated, repeated_created = register_recommendation_event(
            self.profile, self.vacancy, source_analysis=self.analysis
        )

        self.assertTrue(created)
        self.assertFalse(repeated_created)
        self.assertEqual(first.pk, repeated.pk)
        self.assertEqual(RecommendationEvent.objects.filter(profile=self.profile, vacancy=self.vacancy).count(), 1)

    def test_does_not_record_discarded_or_archived_recommendations(self):
        VacancyFollowUp.objects.create(
            profile=self.profile,
            vacancy=self.vacancy,
            status=VacancyFollowUp.Status.DISCARDED,
        )
        event, created = register_recommendation_event(
            self.profile, self.vacancy, source_analysis=self.analysis
        )
        self.assertIsNone(event)
        self.assertFalse(created)

        follow_up = VacancyFollowUp.objects.get(profile=self.profile, vacancy=self.vacancy)
        follow_up.status = VacancyFollowUp.Status.PENDING
        follow_up.archived_at = timezone.now()
        follow_up.save(update_fields=["status", "archived_at", "updated_at"])
        event, created = register_recommendation_event(self.profile, self.vacancy)
        self.assertIsNone(event)
        self.assertFalse(created)

    def test_existing_recommendations_are_baselined_but_explicit_restore_is_new(self):
        self.profile.recommendation_tracking_started_at = timezone.now()
        self.profile.save(update_fields=["recommendation_tracking_started_at"])
        old_time = self.profile.recommendation_tracking_started_at - timedelta(days=1)
        self.analysis.completed_at = old_time
        self.analysis.save(update_fields=["completed_at"])

        event, created = register_recommendation_event(self.profile, self.vacancy)
        self.assertIsNone(event)
        self.assertFalse(created)

        follow_up = VacancyFollowUp.objects.create(
            profile=self.profile,
            vacancy=self.vacancy,
            status=VacancyFollowUp.Status.PENDING,
            state_changed_at=timezone.now(),
        )
        event, created = register_recommendation_event(self.profile, self.vacancy)
        self.assertTrue(created)
        self.assertEqual(event.vacancy_id, self.vacancy.pk)
        follow_up.refresh_from_db()

    def test_profile_and_vacancy_are_isolated(self):
        other_user = get_user_model().objects.create_user("other-recommendation-user")
        other_profile = Profile.objects.create(owner=other_user, revision_number=1, locations=["Bogotá"])
        ProfileRevision.objects.create(profile=other_profile, version=1, locations=["Bogotá"])
        other_analysis = self.make_analysis(other_profile, self.vacancy)

        register_recommendation_event(self.profile, self.vacancy, source_analysis=self.analysis)
        register_recommendation_event(other_profile, self.vacancy, source_analysis=other_analysis)

        self.assertEqual(RecommendationEvent.objects.filter(vacancy=self.vacancy).count(), 2)

    @patch("dashboard.services.current_score_analyses")
    def test_concurrent_registration_keeps_one_event(self, current_analyses):
        current_analyses.return_value = ([self.analysis], self.revision, set())
        barrier = Barrier(2)

        def create_event():
            close_old_connections()
            try:
                barrier.wait(timeout=5)
                event, created = register_recommendation_event(
                    Profile.objects.get(pk=self.profile.pk),
                    Vacancy.objects.get(pk=self.vacancy.pk),
                    source_analysis=VacancyAnalysis.objects.get(pk=self.analysis.pk),
                )
                connections.close_all()
                return event.pk, created
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _index: create_event(), range(2)))

        self.assertEqual(RecommendationEvent.objects.filter(profile=self.profile, vacancy=self.vacancy).count(), 1)
        self.assertEqual(sum(created for _event_id, created in results), 1)

    def test_indicator_uses_visible_pending_events_independent_of_page_filters(self):
        event, _created = register_recommendation_event(
            self.profile, self.vacancy, source_analysis=self.analysis
        )
        summary = new_recommendation_summary(self.profile)
        self.assertEqual(summary, {"count": 1, "cutoff": event.pk})

        VacancyFollowUp.objects.create(
            profile=self.profile,
            vacancy=self.vacancy,
            status=VacancyFollowUp.Status.APPLIED,
        )
        self.assertEqual(new_recommendation_summary(self.profile)["count"], 0)

    def test_review_cutoff_preserves_events_arriving_after_render(self):
        first_vacancy = self.vacancy
        first_event, _created = register_recommendation_event(
            self.profile, first_vacancy, source_analysis=self.analysis
        )
        rendered_cutoff = new_recommendation_summary(self.profile)["cutoff"]

        second_vacancy = self.make_vacancy("https://jobs.example.test/recommendation-2")
        second_analysis = self.make_analysis(self.profile, second_vacancy)
        second_event, _created = register_recommendation_event(
            self.profile, second_vacancy, source_analysis=second_analysis
        )

        mark_recommendations_reviewed(self.profile, rendered_cutoff)
        summary = new_recommendation_summary(Profile.objects.get(pk=self.profile.pk))
        self.assertEqual(summary["count"], 1)
        self.assertEqual(summary["cutoff"], second_event.pk)
        self.assertLess(first_event.pk, second_event.pk)

    def test_review_cutoff_cannot_advance_past_visible_events_or_cross_profiles(self):
        event, _created = register_recommendation_event(
            self.profile, self.vacancy, source_analysis=self.analysis
        )
        other_user = get_user_model().objects.create_user("unrelated-user")
        other_profile = Profile.objects.create(owner=other_user, revision_number=1, locations=["Bogotá"])
        ProfileRevision.objects.create(profile=other_profile, version=1, locations=["Bogotá"])

        mark_recommendations_reviewed(self.profile, event.pk + 100)
        self.profile.refresh_from_db()
        self.assertEqual(new_recommendation_summary(self.profile)["count"], 0)
        self.assertEqual(new_recommendation_summary(other_profile)["count"], 0)

    def test_dashboard_renders_badge_and_explicit_review_action_with_filters(self):
        event, _created = register_recommendation_event(
            self.profile, self.vacancy, source_analysis=self.analysis
        )
        GuidedTourProgress.objects.create(
            owner=self.user,
            version=3,
            status=GuidedTourProgress.Status.SKIPPED,
            mandatory_completed=True,
        )
        self.client.force_login(self.user)

        response = self.client.get("/?state=pending&score_min=4.5&page=3")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-label="1 recomendaciones nuevas"')
        self.assertContains(response, 'name="cutoff" value="%s"' % event.pk)

        response = self.client.post(
            "/novedades/revisar/",
            {"cutoff": event.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.recommendations_reviewed_through, event.pk)

    def test_push_subscription_is_opted_in_per_device_and_reassigned_to_current_account(self):
        endpoint = "https://push.example.test/send/device-token"
        payload = {
            "subscription": {
                "endpoint": endpoint,
                "keys": {"p256dh": "synthetic-public-key", "auth": "synthetic-auth-key"},
            }
        }
        GuidedTourProgress.objects.create(
            owner=self.user,
            version=3,
            status=GuidedTourProgress.Status.SKIPPED,
            mandatory_completed=True,
        )
        self.client.force_login(self.user)
        response = self.client.post(
            "/perfil/notificaciones/suscripcion/",
            json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        first = PushSubscription.objects.get()
        self.assertEqual(first.profile, self.profile)
        self.assertNotEqual(first.endpoint_ciphertext, endpoint)
        self.assertNotIn("synthetic-auth-key", first.auth_ciphertext)
        self.assertEqual(first.endpoint, endpoint)

        second_user = get_user_model().objects.create_user("second-push-user", password="test-password")
        second_profile = Profile.objects.create(owner=second_user)
        GuidedTourProgress.objects.create(
            owner=second_user,
            version=3,
            status=GuidedTourProgress.Status.SKIPPED,
            mandatory_completed=True,
        )
        self.client.force_login(second_user)
        response = self.client.post(
            "/perfil/notificaciones/suscripcion/",
            json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        first.refresh_from_db()
        self.assertEqual(first.profile, second_profile)
        self.assertEqual(PushSubscription.objects.count(), 1)

    def _create_push_subscription(self, *, activated_at=None, last_event_cutoff_id=0):
        endpoint = "https://push.example.test/send/daily-token"
        return PushSubscription.objects.create(
            profile=self.profile,
            endpoint_digest=hashlib.sha256(endpoint.encode("utf-8")).hexdigest(),
            endpoint=endpoint,
            p256dh_key="synthetic-public-key",
            auth_key="synthetic-auth-key",
            activated_at=activated_at or timezone.now() - timedelta(days=1),
            last_event_cutoff_id=last_event_cutoff_id,
        )

    @staticmethod
    def push_time(days_ahead=1, *, hour=9, minute=0):
        local = timezone.now().astimezone(ZoneInfo("America/Bogota"))
        local = (local + timedelta(days=days_ahead)).replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
        return local.astimezone(ZoneInfo("UTC"))

    def test_daily_push_reserves_one_attempt_per_device_and_local_day(self):
        subscription = self._create_push_subscription()
        self.analysis.completed_at = timezone.now()
        self.analysis.save(update_fields=["completed_at"])
        event, created = register_recommendation_event(
            self.profile, self.vacancy, source_analysis=self.analysis
        )
        self.assertTrue(created)
        sender = Mock()
        now = self.push_time()
        event.created_at = now - timedelta(hours=2)
        event.save(update_fields=["created_at"])

        result = send_daily_recommendation_summaries(now=now, sender=sender)
        second = send_daily_recommendation_summaries(now=now, sender=sender)

        self.assertEqual(result["attempted"], 1)
        self.assertEqual(second["attempted"], 0)
        self.assertEqual(sender.call_count, 1)
        self.assertNotIn("title", sender.call_args.args[0])
        self.assertEqual(PushDailyAttempt.objects.filter(subscription=subscription).count(), 1)
        self.assertEqual(PushDailyAttempt.objects.get().status, PushDailyAttempt.Status.SENT)
        next_day = self.push_time(days_ahead=2)
        later = send_daily_recommendation_summaries(now=next_day, sender=sender)
        self.assertEqual(later["attempted"], 0)
        self.assertEqual(sender.call_count, 1)

    def test_daily_push_skips_no_events_reviewed_events_and_outside_window(self):
        subscription = self._create_push_subscription()
        sender = Mock()
        now = self.push_time()
        result = send_daily_recommendation_summaries(now=now, sender=sender)
        self.assertEqual(result["attempted"], 0)

        event, _created = register_recommendation_event(
            self.profile, self.vacancy, source_analysis=self.analysis
        )
        mark_recommendations_reviewed(self.profile, event.pk)
        result = send_daily_recommendation_summaries(now=self.push_time(days_ahead=2), sender=sender)
        self.assertEqual(result["attempted"], 0)

        late = send_daily_recommendation_summaries(
            now=self.push_time(hour=10), sender=sender
        )
        self.assertTrue(late["skipped_outside_window"])
        self.assertEqual(sender.call_count, 0)
        subscription.refresh_from_db()
        self.assertGreaterEqual(subscription.last_event_cutoff_id, event.pk)

    def test_daily_push_does_not_backfill_a_missed_previous_day(self):
        self._create_push_subscription(activated_at=timezone.now() - timedelta(days=2))
        _event, _created = register_recommendation_event(
            self.profile, self.vacancy, source_analysis=self.analysis
        )
        sender = Mock()
        result = send_daily_recommendation_summaries(now=self.push_time(), sender=sender)
        self.assertEqual(result["attempted"], 0)
        self.assertEqual(sender.call_count, 0)

    def test_daily_push_skips_deactivated_accounts(self):
        self._create_push_subscription()
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        sender = Mock()
        result = send_daily_recommendation_summaries(now=self.push_time(), sender=sender)
        self.assertEqual(result["attempted"], 0)
        self.assertEqual(sender.call_count, 0)
        self.assertEqual(PushDailyAttempt.objects.count(), 0)

    def test_daily_push_never_retries_ambiguous_failure_and_deletes_expired_subscription(self):
        subscription = self._create_push_subscription()
        event, _created = register_recommendation_event(
            self.profile, self.vacancy, source_analysis=self.analysis
        )
        sender = Mock(side_effect=TimeoutError("synthetic"))
        now = self.push_time()
        event.created_at = now - timedelta(hours=2)
        event.save(update_fields=["created_at"])

        send_daily_recommendation_summaries(now=now, sender=sender)
        send_daily_recommendation_summaries(now=now, sender=sender)
        self.assertEqual(sender.call_count, 1)
        attempt = PushDailyAttempt.objects.get()
        self.assertEqual(attempt.status, PushDailyAttempt.Status.FAILED)
        self.assertEqual(attempt.failure_category, "push_error")

        subscription.refresh_from_db()
        next_vacancy = self.make_vacancy("https://jobs.example.test/recommendation-expired")
        next_analysis = self.make_analysis(self.profile, next_vacancy)
        next_event, _created = register_recommendation_event(
            self.profile, next_vacancy, source_analysis=next_analysis
        )
        next_date = self.push_time(days_ahead=2)
        next_event.created_at = next_date - timedelta(hours=2)
        next_event.save(update_fields=["created_at"])
        subscription.last_event_cutoff_id = next_event.pk - 1
        subscription.save(update_fields=["last_event_cutoff_id"])
        expired = RuntimeError("synthetic expired")
        expired.status_code = 410
        sender = Mock(side_effect=expired)
        send_daily_recommendation_summaries(now=next_date, sender=sender)
        self.assertFalse(PushSubscription.objects.filter(pk=subscription.pk).exists())
        self.assertTrue(PushDailyAttempt.objects.filter(
            subscription_digest=subscription.endpoint_digest,
            local_date=next_date.astimezone(ZoneInfo("America/Bogota")).date(),
            status=PushDailyAttempt.Status.FAILED,
            failure_category="expired",
        ).exists())

    def test_logout_unlinks_only_current_device_and_subscription(self):
        endpoint = "https://push.example.test/send/logout-token"
        subscription = PushSubscription.objects.create(
            profile=self.profile,
            endpoint_digest=hashlib.sha256(endpoint.encode("utf-8")).hexdigest(),
            endpoint=endpoint,
            p256dh_key="synthetic-public-key",
            auth_key="synthetic-auth-key",
        )
        self.client.force_login(self.user)
        response = self.client.post("/accounts/logout/", {"push_endpoint": endpoint})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PushSubscription.objects.filter(pk=subscription.pk).exists())

    def test_push_worker_is_generic_no_store_and_does_not_intercept_fetch(self):
        response = self.client.get("/push-worker.js")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Service-Worker-Allowed"], "/")
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertContains(response, "silent: true")
        self.assertContains(response, "Hay recomendaciones nuevas.")
        self.assertContains(response, "new URL('/', self.location.origin)")
        self.assertNotContains(response, "addEventListener('fetch'")
        self.assertNotContains(response, "caches.")

    @override_settings(
        PUSH_VAPID_PUBLIC_KEY="synthetic-public-vapid",
        PUSH_VAPID_PRIVATE_KEY="synthetic-private-vapid",
        PUSH_VAPID_SUBJECT="mailto:test@example.invalid",
    )
    @patch("pywebpush.webpush")
    def test_push_sender_uses_short_ttl_and_never_includes_vacancy_content(self, webpush):
        subscription_info = {
            "endpoint": "https://push.example.test/send/private-device-token",
            "keys": {"p256dh": "private-public-key", "auth": "private-auth-key"},
        }
        _send_generic_push(subscription_info)
        call = webpush.call_args.kwargs
        self.assertEqual(call["ttl"], 300)
        self.assertEqual(call["timeout"], 8)
        self.assertEqual(call["vapid_claims"], {"sub": "mailto:test@example.invalid"})
        self.assertEqual(call["data"], '{"type": "recommendations"}')
        self.assertNotIn("private-device-token", call["data"])
        self.assertNotIn("private-public-key", call["data"])
