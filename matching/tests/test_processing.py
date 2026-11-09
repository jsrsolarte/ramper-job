from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connections
from django.test import TestCase, override_settings
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from dashboard.models import VacancyFollowUp
from jobs.models import Vacancy
from matching.client import OmniRouteError
from matching.models import (
    AICallAttempt,
    PROMPT_VERSION,
    RUBRIC_VERSION,
    MatchingConfig,
    ProfileVacancyDiscovery,
    VacancyAnalysis,
)
from matching.tasks import (
    analyze_vacancy_for_profile,
    create_analysis,
    organize_vacancy,
    reconcile_pending_analyses_task,
    schedule_eligible_organizations,
    schedule_profile_analyses,
    schedule_vacancy_analysis,
)
from profiles.models import Profile, ProfileRevision
from profiles.tests.helpers import mark_tour_completed
from matching.recovery import claim_analysis
from matching.schemas import InvalidAnalysisError
from operations.models import OperationalRun


class MatchingProcessingTests(TestCase):
    def setUp(self):
        organization_dispatch = patch("matching.tasks.organize_vacancy.delay")
        self.organization_dispatch = organization_dispatch.start()
        self.addCleanup(organization_dispatch.stop)
        user = get_user_model().objects.create_user("member")
        mark_tour_completed(user)
        self.profile = Profile.objects.create(
            owner=user, search_phrases=["Analista de datos"], locations=["Bogotá"],
            cv_file="profiles/1/cv/v1.docx", revision_number=1
        )
        self.revision = ProfileRevision.objects.create(
            profile=self.profile,
            version=1,
            search_phrases=["Analista de datos"],
            locations=["Bogotá"],
            cv_file_path=self.profile.cv_file.name,
        )
        self.vacancy = Vacancy.objects.create(
            source="elempleo_co",
            title="Analista de datos",
            location="Bogotá",
            description="Experiencia con SQL",
            raw_data={"details": {"city": "Bogotá", "modality": "presencial", "education": "Universitaria"}},
            original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-123",
        )
        self.config = MatchingConfig.objects.create(
            version=1,
            rubric_version=RUBRIC_VERSION,
            prompt_version=PROMPT_VERSION,
            analysis_prompt="Evalúa coincidencia",
            organization_prompt="Organiza descripción",
        )
        self.analysis = create_analysis(self.profile, self.vacancy, self.config)

    @patch("matching.tasks.request_model_analysis")
    @patch("matching.tasks.extract_revision_text", return_value="CV extraído")
    def test_worker_completes_valid_analysis_for_profile(self, extract, request):
        request.return_value = {
            "organized_description": {
                "summary": "Responsabilidades de análisis.",
                "keywords": ["SQL"],
                "responsibilities": ["Analizar información"],
                "requirements": ["Experiencia con SQL"],
                "conditions": [],
            },
            "rubric_version": RUBRIC_VERSION,
            "critical_requirements": [],
            "score_breakdown": {
                "skills": {"score": 4, "status": "cumple", "evidence": "Experiencia con SQL"},
                "experience": {"score": 2, "status": "cumple", "evidence": "Analizar información"},
                "alignment": {"score": 2, "status": "cumple", "evidence": "Cargo de análisis"},
                "education": {"score": 1, "status": "cumple", "evidence": "Educación universitaria"},
                "profile_criteria": {"score": 1, "status": "cumple", "evidence": "Criterios del perfil considerados"},
            },
            "reasons": ["Coincide SQL"],
            "gaps": [],
        }

        result = analyze_vacancy_for_profile.apply(args=(self.analysis.pk,), throw=True)

        self.analysis.refresh_from_db()
        self.assertEqual(result.result, self.analysis.pk)
        self.assertEqual(self.analysis.status, VacancyAnalysis.Status.COMPLETED)
        self.assertEqual(self.analysis.profile_revision, self.revision)
        self.assertEqual(self.analysis.score, 10)
        self.assertEqual(self.analysis.organization_status, VacancyAnalysis.OrganizationStatus.PENDING)
        attempt = AICallAttempt.objects.get(analysis=self.analysis)
        self.assertEqual(attempt.stage, AICallAttempt.Stage.SCORING)
        self.assertEqual(attempt.outcome, AICallAttempt.Outcome.SUCCEEDED)
        run = OperationalRun.objects.get(operation="vacancy_analysis")
        self.assertEqual(run.status, OperationalRun.Status.SUCCEEDED)
        self.assertEqual(run.item_count, 1)
        request.assert_called_once()
        self.assertEqual(request.call_args.kwargs["locations"], [
            "Bogotá", "Soacha", "Chía", "Cajicá", "Cota", "Funza", "Madrid", "Mosquera",
            "La Calera", "Tenjo", "Facatativá", "Zipaquirá",
        ])
        self.assertEqual(request.call_args.kwargs["vacancy"]["details"]["education"], "Universitaria")
        self.assertEqual(request.call_args.kwargs["vacancy"]["description"], "Experiencia con SQL")

    @patch("matching.tasks.request_model_analysis", side_effect=OmniRouteError("Servicio no disponible"))
    @patch("matching.tasks.extract_revision_text", return_value="CV extraído")
    def test_model_outage_leaves_analysis_pending_for_retry(self, extract, request):
        from celery.exceptions import Retry

        with patch.object(analyze_vacancy_for_profile, "retry", side_effect=Retry()):
            with self.assertRaises(Retry):
                analyze_vacancy_for_profile.run(self.analysis.pk)

        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, VacancyAnalysis.Status.PENDING)
        self.assertIn("no disponible", self.analysis.error_message)
        self.assertIsNone(self.analysis.processing_started_at)
        run = OperationalRun.objects.get(operation="vacancy_analysis")
        self.assertEqual(run.status, OperationalRun.Status.RETRYING)
        attempt = AICallAttempt.objects.get(analysis=self.analysis)
        self.assertEqual(attempt.outcome, AICallAttempt.Outcome.RETRYING)
        self.assertIsNone(attempt.input_tokens)
        self.assertIsNone(attempt.output_tokens)

    @patch("matching.tasks.request_model_analysis", return_value={"private_sentinel": "do not persist"})
    @patch("matching.tasks.extract_revision_text", return_value="CV extraído")
    def test_invalid_rubric_response_records_safe_code_and_generic_message(self, extract, request):
        with self.assertRaises(InvalidAnalysisError):
            analyze_vacancy_for_profile.run(self.analysis.pk)

        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, VacancyAnalysis.Status.PENDING)
        self.assertEqual(self.analysis.error_message, "La respuesta de IA no cumple el formato esperado.")
        attempt = AICallAttempt.objects.get(analysis=self.analysis)
        self.assertEqual(attempt.error_category, "analysis.rubric.version")
        self.assertNotIn("private_sentinel", attempt.error_category)
        self.assertNotIn("do not persist", attempt.error_category)
        run = OperationalRun.objects.get(operation="vacancy_analysis")
        self.assertEqual(run.error_category, "analysis.rubric.version")

    @patch("matching.tasks.request_model_organization")
    @patch("matching.tasks.request_model_analysis")
    @patch("matching.tasks.extract_revision_text", return_value="CV extraído")
    def test_discovery_threshold_auto_discards_and_profile_change_does_not_reopen_it(
        self, extract, score_call, organization_call
    ):
        # The saved threshold belongs to this discovery, even if the profile
        # preference changes before its analysis finishes.
        ProfileVacancyDiscovery.objects.filter(
            profile=self.profile, vacancy=self.vacancy,
        ).update(auto_discard_threshold=9, auto_discard_evaluated_at=None)
        self.profile.min_score = 7
        self.profile.save(update_fields=["min_score"])
        payload = self._valid_payload()
        payload["score_breakdown"]["skills"] = {
            "score": 2, "status": "parcial", "evidence": "Experiencia relacionada",
        }
        score_call.return_value = payload
        organization_call.return_value = {
            "summary": "Responsabilidades clave", "keywords": ["Mejora continua"],
            "responsibilities": [], "requirements": [], "conditions": [],
        }

        analyze_vacancy_for_profile.apply(args=(self.analysis.pk,), throw=True)
        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, VacancyAnalysis.Status.COMPLETED)
        self.assertEqual(self.analysis.score, 8)
        self.assertEqual(self.analysis.organization_status, VacancyAnalysis.OrganizationStatus.DEFERRED)
        follow_up = VacancyFollowUp.objects.get(profile=self.profile, vacancy=self.vacancy)
        self.assertEqual(follow_up.status, VacancyFollowUp.Status.DISCARDED)
        self.organization_dispatch.assert_not_called()

        self.profile.min_score = 5
        self.profile.save(update_fields=["min_score"])
        with self.captureOnCommitCallbacks(execute=True):
            organization_ids = schedule_eligible_organizations.run(self.profile.pk)
        self.assertEqual(organization_ids, [])
        self.organization_dispatch.assert_not_called()

        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.score, 8)
        follow_up.refresh_from_db()
        self.assertEqual(self.analysis.organization_status, VacancyAnalysis.OrganizationStatus.DEFERRED)
        self.assertEqual(follow_up.status, VacancyFollowUp.Status.DISCARDED)
        organization_call.assert_not_called()

    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    def test_profile_scheduling_creates_one_analysis_per_vacancy(self, queue):
        with self.captureOnCommitCallbacks(execute=True):
            result = schedule_profile_analyses.run(self.profile.pk)

        self.assertEqual(len(result), 1)
        self.assertEqual(VacancyAnalysis.objects.filter(profile=self.profile).count(), 1)
        queue.assert_called_once_with(self.analysis.pk)

    def test_vacancy_scheduling_ignores_missing_or_inactive_vacancy(self):
        self.assertEqual(schedule_vacancy_analysis.run(self.vacancy.pk + 999999), [])

        self.vacancy.is_active = False
        self.vacancy.save(update_fields=["is_active"])
        self.assertEqual(schedule_vacancy_analysis.run(self.vacancy.pk), [])

    def test_analysis_is_not_created_for_a_profile_outside_published_city(self):
        self.revision.locations = ["Medellín"]
        self.revision.save(update_fields=["locations"])

        self.assertIsNone(create_analysis(self.profile, self.vacancy, self.config))

    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    def test_vacancy_scheduling_only_queues_geographically_eligible_profiles(self, queue):
        other_user = get_user_model().objects.create_user("medellin-member")
        other_profile = Profile.objects.create(
            owner=other_user, locations=["Medellín"], cv_file="profiles/2/cv/v1.pdf", revision_number=1
        )
        other_revision = ProfileRevision.objects.create(
            profile=other_profile, version=1, locations=["Medellín"], cv_file_path=other_profile.cv_file.name
        )

        with self.captureOnCommitCallbacks(execute=True):
            queued = schedule_vacancy_analysis.run(self.vacancy.pk)

        self.assertEqual(len(queued), 1)
        self.assertEqual(VacancyAnalysis.objects.filter(vacancy=self.vacancy).count(), 1)
        self.assertEqual(VacancyAnalysis.objects.get(vacancy=self.vacancy).profile, self.profile)
        self.assertNotEqual(VacancyAnalysis.objects.get(vacancy=self.vacancy).profile_revision, other_revision)
        queue.assert_called_once()

    @patch("matching.tasks.request_model_analysis")
    @patch("matching.tasks.extract_revision_text", return_value="CV extraído")
    def test_duplicate_delivery_after_completion_does_not_call_model_twice(self, extract, request):
        request.return_value = self._valid_payload()

        with self.captureOnCommitCallbacks(execute=True):
            analyze_vacancy_for_profile.apply(args=(self.analysis.pk,), throw=True)
            analyze_vacancy_for_profile.apply(args=(self.analysis.pk,), throw=True)

        request.assert_called_once()

    def test_only_one_worker_can_claim_an_analysis(self):
        first = claim_analysis(self.analysis.pk)
        second = claim_analysis(self.analysis.pk)

        self.assertIsNotNone(first)
        self.assertIsNone(second)

    def test_expired_worker_lease_can_be_claimed_again(self):
        expired = timezone.now() - timedelta(hours=1)
        VacancyAnalysis.objects.filter(pk=self.analysis.pk).update(processing_started_at=expired)

        claimed = claim_analysis(self.analysis.pk)

        self.assertIsNotNone(claimed)
        self.assertGreater(claimed.processing_started_at, expired)

    def test_completed_or_superseded_analysis_cannot_be_claimed(self):
        self.analysis.status = VacancyAnalysis.Status.COMPLETED
        self.analysis.save(update_fields=("status",))
        self.assertIsNone(claim_analysis(self.analysis.pk))

        self.analysis.status = VacancyAnalysis.Status.SUPERSEDED
        self.analysis.save(update_fields=("status",))
        self.assertIsNone(claim_analysis(self.analysis.pk))

    @override_settings(
        ANALYSIS_RECOVERY_STALE_SECONDS=60,
        ANALYSIS_RECOVERY_LEASE_SECONDS=120,
        ANALYSIS_RECOVERY_MAX_RETRIES=2,
        ANALYSIS_RECOVERY_BATCH_SIZE=10,
    )
    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    def test_reconciler_requeues_an_orphaned_current_analysis(self, queue):
        old = timezone.now() - timedelta(minutes=5)
        VacancyAnalysis.objects.filter(pk=self.analysis.pk).update(created_at=old)

        with self.captureOnCommitCallbacks(execute=True):
            result = reconcile_pending_analyses_task.run()

        self.analysis.refresh_from_db()
        self.assertEqual(result, {"recovered": 1, "exhausted": 0})
        self.assertEqual(self.analysis.recovery_count, 1)
        self.assertIsNotNone(self.analysis.last_enqueued_at)
        queue.assert_called_once_with(self.analysis.pk)
        run = OperationalRun.objects.get(operation="analysis_recovery")
        self.assertEqual(run.status, OperationalRun.Status.SUCCEEDED)
        self.assertEqual(run.item_count, 1)

    @override_settings(
        ANALYSIS_RECOVERY_STALE_SECONDS=60,
        ANALYSIS_RECOVERY_LEASE_SECONDS=120,
        ANALYSIS_RECOVERY_MAX_RETRIES=2,
        ANALYSIS_RECOVERY_BATCH_SIZE=10,
    )
    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    def test_repeated_reconciliation_does_not_duplicate_a_recent_dispatch(self, queue):
        old = timezone.now() - timedelta(minutes=5)
        VacancyAnalysis.objects.filter(pk=self.analysis.pk).update(created_at=old)

        with self.captureOnCommitCallbacks(execute=True):
            first = reconcile_pending_analyses_task.run()
            second = reconcile_pending_analyses_task.run()

        self.assertEqual(first, {"recovered": 1, "exhausted": 0})
        self.assertEqual(second, {"recovered": 0, "exhausted": 0})
        queue.assert_called_once_with(self.analysis.pk)

    @override_settings(
        ANALYSIS_RECOVERY_STALE_SECONDS=60,
        ANALYSIS_RECOVERY_LEASE_SECONDS=120,
        ANALYSIS_RECOVERY_MAX_RETRIES=2,
        ANALYSIS_RECOVERY_BATCH_SIZE=10,
    )
    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    def test_reconciler_returns_zero_for_an_empty_queue(self, queue):
        self.analysis.status = VacancyAnalysis.Status.COMPLETED
        self.analysis.save(update_fields=("status",))

        result = reconcile_pending_analyses_task.run()

        self.assertEqual(result, {"recovered": 0, "exhausted": 0})
        queue.assert_not_called()

    @override_settings(
        ANALYSIS_RECOVERY_STALE_SECONDS=60,
        ANALYSIS_RECOVERY_LEASE_SECONDS=120,
        ANALYSIS_RECOVERY_MAX_RETRIES=2,
        ANALYSIS_RECOVERY_BATCH_SIZE=10,
    )
    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    def test_dispatch_failure_is_recovered_after_the_persisted_timestamp_stales(self, queue):
        from matching.recovery import enqueue_analysis

        queue.side_effect = [RuntimeError("broker unavailable"), None]
        with self.assertRaises(RuntimeError):
            with self.captureOnCommitCallbacks(execute=True):
                enqueue_analysis(self.analysis.pk)

        self.analysis.refresh_from_db()
        self.assertIsNotNone(self.analysis.last_enqueued_at)
        old = timezone.now() - timedelta(minutes=5)
        VacancyAnalysis.objects.filter(pk=self.analysis.pk).update(
            last_enqueued_at=old, created_at=old
        )
        with self.captureOnCommitCallbacks(execute=True):
            result = reconcile_pending_analyses_task.run()

        self.assertEqual(result, {"recovered": 1, "exhausted": 0})
        self.assertEqual(queue.call_count, 2)

    @override_settings(
        ANALYSIS_RECOVERY_STALE_SECONDS=60,
        ANALYSIS_RECOVERY_LEASE_SECONDS=120,
        ANALYSIS_RECOVERY_MAX_RETRIES=2,
        ANALYSIS_RECOVERY_BATCH_SIZE=10,
    )
    @patch("matching.tasks.request_model_analysis")
    @patch("matching.tasks.extract_revision_text", return_value="CV extraído")
    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    def test_recovered_analysis_completes_and_appears_on_applicant_dashboard(
        self, queue, extract, request
    ):
        request.return_value = self._valid_payload()
        old = timezone.now() - timedelta(minutes=5)
        VacancyAnalysis.objects.filter(pk=self.analysis.pk).update(created_at=old)

        with self.captureOnCommitCallbacks(execute=True):
            result = reconcile_pending_analyses_task.run()
        self.assertEqual(result, {"recovered": 1, "exhausted": 0})
        queue.assert_called_once_with(self.analysis.pk)

        analyze_vacancy_for_profile.apply(args=(self.analysis.pk,), throw=True)
        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, VacancyAnalysis.Status.COMPLETED)
        self.assertIsNone(self.analysis.processing_started_at)

        self.client.force_login(self.profile.owner)
        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.vacancy.title)

    @override_settings(
        ANALYSIS_RECOVERY_STALE_SECONDS=60,
        ANALYSIS_RECOVERY_LEASE_SECONDS=120,
        ANALYSIS_RECOVERY_MAX_RETRIES=1,
        ANALYSIS_RECOVERY_BATCH_SIZE=10,
    )
    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    def test_reconciler_retries_after_previous_limit(self, queue):
        old = timezone.now() - timedelta(minutes=5)
        VacancyAnalysis.objects.filter(pk=self.analysis.pk).update(
            created_at=old,
            last_enqueued_at=old,
            recovery_count=1,
        )

        with self.captureOnCommitCallbacks(execute=True):
            result = reconcile_pending_analyses_task.run()

        self.analysis.refresh_from_db()
        self.assertEqual(result, {"recovered": 1, "exhausted": 0})
        self.assertEqual(self.analysis.status, VacancyAnalysis.Status.PENDING)
        queue.assert_called_once_with(self.analysis.pk)

    @override_settings(
        ANALYSIS_RECOVERY_STALE_SECONDS=60,
        ANALYSIS_RECOVERY_LEASE_SECONDS=120,
        ANALYSIS_RECOVERY_MAX_RETRIES=1,
        ANALYSIS_RECOVERY_BATCH_SIZE=10,
    )
    @patch("matching.tasks.request_model_analysis", side_effect=OmniRouteError("Servicio no disponible"))
    @patch("matching.tasks.extract_revision_text", return_value="CV extraído")
    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    def test_persistent_gateway_failure_continues_recovering(
        self, queue, extract, request
    ):
        from celery.exceptions import Retry

        old = timezone.now() - timedelta(minutes=5)
        VacancyAnalysis.objects.filter(pk=self.analysis.pk).update(created_at=old)
        with self.captureOnCommitCallbacks(execute=True):
            first_recovery = reconcile_pending_analyses_task.run()
        self.assertEqual(first_recovery, {"recovered": 1, "exhausted": 0})

        with patch.object(analyze_vacancy_for_profile, "retry", side_effect=Retry()):
            with self.assertRaises(Retry):
                analyze_vacancy_for_profile.run(self.analysis.pk)

        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, VacancyAnalysis.Status.PENDING)
        self.assertIsNone(self.analysis.processing_started_at)
        VacancyAnalysis.objects.filter(pk=self.analysis.pk).update(
            last_enqueued_at=old, created_at=old
        )
        with self.captureOnCommitCallbacks(execute=True):
            recovered = reconcile_pending_analyses_task.run()

        self.analysis.refresh_from_db()
        self.assertEqual(recovered, {"recovered": 1, "exhausted": 0})
        self.assertEqual(self.analysis.status, VacancyAnalysis.Status.PENDING)
        self.assertEqual(queue.call_count, 2)

    @override_settings(
        ANALYSIS_RECOVERY_STALE_SECONDS=60,
        ANALYSIS_RECOVERY_LEASE_SECONDS=120,
        ANALYSIS_RECOVERY_MAX_RETRIES=2,
        ANALYSIS_RECOVERY_BATCH_SIZE=10,
    )
    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    def test_reconciler_skips_recent_dispatch_and_active_lease(self, queue):
        now = timezone.now()
        VacancyAnalysis.objects.filter(pk=self.analysis.pk).update(
            last_enqueued_at=now,
            processing_started_at=now,
        )

        result = reconcile_pending_analyses_task.run()

        self.assertEqual(result, {"recovered": 0, "exhausted": 0})
        queue.assert_not_called()

    @override_settings(
        ANALYSIS_RECOVERY_STALE_SECONDS=60,
        ANALYSIS_RECOVERY_LEASE_SECONDS=120,
        ANALYSIS_RECOVERY_MAX_RETRIES=2,
        ANALYSIS_RECOVERY_BATCH_SIZE=1,
    )
    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    def test_reconciler_respects_batch_limit(self, queue):
        second = create_analysis(self.profile, self.vacancy, self.config, force=True)
        old = timezone.now() - timedelta(minutes=5)
        VacancyAnalysis.objects.filter(pk__in=(self.analysis.pk, second.pk)).update(created_at=old)

        with self.captureOnCommitCallbacks(execute=True):
            result = reconcile_pending_analyses_task.run()

        self.assertEqual(result, {"recovered": 1, "exhausted": 0})
        self.assertEqual(queue.call_count, 1)

    @override_settings(
        ANALYSIS_RECOVERY_STALE_SECONDS=60,
        ANALYSIS_RECOVERY_LEASE_SECONDS=120,
        ANALYSIS_RECOVERY_MAX_RETRIES=2,
        ANALYSIS_RECOVERY_BATCH_SIZE=10,
    )
    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    def test_reconciler_skips_old_profile_revision_inactive_vacancy_and_wrong_location(self, queue):
        self.profile.revision_number = 2
        self.profile.save(update_fields=("revision_number",))
        current_revision = ProfileRevision.objects.create(
            profile=self.profile,
            version=2,
            search_phrases=["Analista de datos"],
            locations=["Medellín"],
            cv_file_path=self.profile.cv_file.name,
        )
        inactive_vacancy = Vacancy.objects.create(
            source="elempleo_co", title="Analista inactiva", location="Medellín", is_active=False,
            original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-456",
        )
        wrong_location_vacancy = Vacancy.objects.create(
            source="elempleo_co", title="Analista Bogotá", location="Bogotá", is_active=True,
            original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-789",
        )
        inactive = VacancyAnalysis.objects.create(
            profile=self.profile, profile_revision=current_revision, vacancy=inactive_vacancy,
            matching_config=self.config,
        )
        wrong_location = VacancyAnalysis.objects.create(
            profile=self.profile, profile_revision=current_revision, vacancy=wrong_location_vacancy,
            matching_config=self.config,
        )
        old = timezone.now() - timedelta(minutes=5)
        VacancyAnalysis.objects.filter(
            pk__in=(self.analysis.pk, inactive.pk, wrong_location.pk)
        ).update(created_at=old)

        result = reconcile_pending_analyses_task.run()

        self.assertEqual(result, {"recovered": 0, "exhausted": 0})
        queue.assert_not_called()

    def _valid_payload(self):
        return {
            "rubric_version": RUBRIC_VERSION,
            "critical_requirements": [],
            "score_breakdown": {
                "skills": {"score": 4, "status": "cumple", "evidence": "Experiencia con SQL"},
                "experience": {"score": 2, "status": "cumple", "evidence": "Analizar información"},
                "alignment": {"score": 2, "status": "cumple", "evidence": "Cargo de análisis"},
                "education": {"score": 1, "status": "cumple", "evidence": "Educación universitaria"},
                "profile_criteria": {"score": 1, "status": "cumple", "evidence": "Criterios del perfil considerados"},
            },
            "reasons": ["Coincide SQL"],
            "gaps": [],
        }


class ConcurrentAnalysisClaimTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        user = get_user_model().objects.create_user("concurrent-member")
        profile = Profile.objects.create(
            owner=user, locations=["Bogotá"], cv_file="profiles/1/cv/v1.pdf", revision_number=1
        )
        revision = ProfileRevision.objects.create(
            profile=profile, version=1, locations=["Bogotá"], cv_file_path=profile.cv_file.name
        )
        vacancy = Vacancy.objects.create(
            source="elempleo_co", title="Analista", location="Bogotá",
            original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-concurrente",
        )
        config = MatchingConfig.objects.create(
            version=1, rubric_version=RUBRIC_VERSION, prompt_version=PROMPT_VERSION, analysis_prompt="Evalúa", organization_prompt="Organiza"
        )
        self.analysis = VacancyAnalysis.objects.create(
            profile=profile, profile_revision=revision, vacancy=vacancy, matching_config=config
        )

    @patch("matching.tasks.request_model_analysis")
    @patch("matching.tasks.extract_revision_text", return_value="CV extraído")
    def test_simultaneous_workers_call_the_model_once(self, extract, request):
        request.return_value = MatchingProcessingTests._valid_payload(self)
        barrier = Barrier(2)

        def run_worker():
            try:
                barrier.wait(timeout=5)
                return analyze_vacancy_for_profile.run(self.analysis.pk)
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda _: run_worker(), range(2)))

        self.assertCountEqual(results, [self.analysis.pk, None])
        request.assert_called_once()
        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, VacancyAnalysis.Status.COMPLETED)
