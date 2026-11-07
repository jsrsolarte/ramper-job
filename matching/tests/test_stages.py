from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings

from jobs.models import Vacancy
from matching.client import ModelCallResult, request_model_organization
from matching.models import AICallAttempt, RUBRIC_VERSION, MatchingConfig, VacancyAnalysis, VacancyOrganization
from matching.tasks import (
    organize_vacancy,
    queue_organization,
    retry_failed_organizations,
    schedule_eligible_organizations,
)
from profiles.models import Profile, ProfileRevision


class StagedAnalysisTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("member")
        self.profile = Profile.objects.create(
            owner=user, revision_number=1, min_score=7, cv_file="profiles/1/cv/v1.pdf"
        )
        revision = ProfileRevision.objects.create(profile=self.profile, version=1)
        self.vacancy = Vacancy.objects.create(
            source="elempleo_co", title="Analista de procesos", description="Mejora continua",
            original_url="https://www.elempleo.com/co/ofertas-trabajo/procesos-1",
        )
        self.config = MatchingConfig.objects.create(
            version=1, rubric_version=RUBRIC_VERSION, analysis_prompt="Evalúa",
            organization_prompt="Resume los datos de la publicación",
        )
        self.analysis = VacancyAnalysis.objects.create(
            profile=self.profile, profile_revision=revision, vacancy=self.vacancy,
            matching_config=self.config, status=VacancyAnalysis.Status.COMPLETED, score=8,
        )

    @patch("matching.tasks.organize_vacancy.delay")
    def test_multiple_profiles_share_one_vacancy_config_content_organization(self, dispatch):
        with self.captureOnCommitCallbacks(execute=True):
            first = queue_organization(self.analysis)
            other_user = get_user_model().objects.create_user("relative")
            other_profile = Profile.objects.create(owner=other_user, revision_number=1, min_score=6)
            revision = ProfileRevision.objects.create(profile=other_profile, version=1)
            second = VacancyAnalysis.objects.create(
                profile=other_profile, profile_revision=revision, vacancy=self.vacancy,
                matching_config=self.config, status=VacancyAnalysis.Status.COMPLETED, score=9,
            )

            shared = queue_organization(second)

        self.assertEqual(first.pk, shared.pk)
        self.assertEqual(VacancyOrganization.objects.count(), 1)
        self.assertEqual(dispatch.call_count, 1)
        second.refresh_from_db()
        self.assertEqual(second.organization_status, VacancyAnalysis.OrganizationStatus.PENDING)

    @patch("matching.tasks.request_model_organization")
    def test_organization_completes_without_profile_data_and_records_usage(self, call_model):
        organization = queue_organization(self.analysis)
        call_model.return_value = ModelCallResult(
            content={"summary": "Mejora procesos", "keywords": ["Procesos"],
                     "responsibilities": [], "requirements": [], "conditions": []},
            input_tokens=120, output_tokens=40,
        )

        organize_vacancy.apply(args=(organization.pk,), throw=True)

        self.analysis.refresh_from_db()
        organization.refresh_from_db()
        attempt = AICallAttempt.objects.get(organization=organization)
        self.assertEqual(self.analysis.score, 8)
        self.assertEqual(self.analysis.organization_status, VacancyAnalysis.OrganizationStatus.COMPLETED)
        self.assertEqual(organization.content["keywords"], ["Procesos"])
        self.assertEqual(attempt.stage, AICallAttempt.Stage.ORGANIZATION)
        self.assertEqual(attempt.input_tokens, 120)
        self.assertEqual(attempt.output_tokens, 40)
        call_model.assert_called_once()
        kwargs = call_model.call_args.kwargs
        self.assertNotIn("profile", kwargs)
        self.assertNotIn("cv", kwargs)
        self.assertEqual(kwargs["vacancy"]["description"], "Mejora continua")

    @override_settings(OMNIROUTE_BASE_URL="http://omniroute.internal/v1", OMNIROUTE_MODEL="auto")
    @patch("matching.client.requests.post")
    def test_organization_request_payload_contains_only_vacancy_and_response_format(self, post):
        response = post.return_value
        response.json.return_value = {
            "choices": [{"message": {"content": '{"summary": "Resumen"}'}}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 7},
        }

        result = request_model_organization(
            vacancy={"title": "Analista"}, prompt="Organiza", parameters={"temperature": 0.1}
        )

        import json
        sent = json.loads(post.call_args.kwargs["json"]["messages"][1]["content"])
        self.assertEqual(set(sent), {"vacancy", "response_format"})
        self.assertEqual(result.input_tokens, 11)
        self.assertEqual(result.output_tokens, 7)

    @patch("matching.tasks.organize_vacancy.delay")
    def test_changing_profile_threshold_does_not_requeue_existing_vacancies(self, dispatch):
        self.profile.min_score = 9
        self.profile.save(update_fields=["min_score"])
        self.assertEqual(schedule_eligible_organizations.run(self.profile.pk), [])

        self.profile.min_score = 7
        self.profile.save(update_fields=["min_score"])
        with self.captureOnCommitCallbacks(execute=True):
            queued = schedule_eligible_organizations.run(self.profile.pk)

        self.assertEqual(queued, [])
        self.assertEqual(dispatch.call_count, 0)
        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.score, 8)
        self.assertEqual(self.analysis.organization_status, VacancyAnalysis.OrganizationStatus.DEFERRED)

    def test_content_or_config_change_uses_a_new_organization_version(self):
        first = queue_organization(self.analysis)
        Vacancy.objects.filter(pk=self.vacancy.pk).update(description="Nuevo contenido de la publicación")
        self.vacancy.refresh_from_db()
        second = queue_organization(self.analysis)
        self.assertNotEqual(first.content_hash, second.content_hash)

        other_config = MatchingConfig.objects.create(
            version=2, rubric_version=RUBRIC_VERSION, analysis_prompt="Nuevo análisis",
            organization_prompt="Nueva organización", is_active=False,
        )
        self.analysis.matching_config = other_config
        self.analysis.save(update_fields=["matching_config"])
        third = queue_organization(self.analysis)

        self.assertNotEqual(second.pk, third.pk)
        self.assertNotEqual(second.matching_config_id, third.matching_config_id)
        self.assertEqual(VacancyOrganization.objects.count(), 3)

    def test_failed_organizations_from_inactive_config_are_not_retried(self):
        old_config = MatchingConfig.objects.create(
            version=2,
            rubric_version=RUBRIC_VERSION,
            analysis_prompt="Anterior",
            organization_prompt="Formato anterior",
            is_active=False,
        )
        organization = VacancyOrganization.objects.create(
            vacancy=self.vacancy,
            matching_config=old_config,
            content_hash="a" * 64,
            status=VacancyOrganization.Status.FAILED,
        )

        self.assertEqual(retry_failed_organizations.run(), 0)

        organization.refresh_from_db()
        self.assertEqual(organization.status, VacancyOrganization.Status.FAILED)
        self.assertEqual(organization.recovery_count, 0)


class ConcurrentOrganizationQueueTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.config = MatchingConfig.objects.create(
            version=1, rubric_version=RUBRIC_VERSION, analysis_prompt="Evalúa", organization_prompt="Organiza"
        )
        self.vacancy = Vacancy.objects.create(
            source="elempleo_co", title="Analista", description="Procesos",
            original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-shared",
        )
        self.analyses = []
        for username in ("one", "two"):
            user = get_user_model().objects.create_user(username)
            profile = Profile.objects.create(owner=user, revision_number=1, min_score=5)
            revision = ProfileRevision.objects.create(profile=profile, version=1)
            self.analyses.append(VacancyAnalysis.objects.create(
                profile=profile, profile_revision=revision, vacancy=self.vacancy, matching_config=self.config,
                status=VacancyAnalysis.Status.COMPLETED, score=8,
            ).pk)

    @patch("matching.tasks.organize_vacancy.delay")
    def test_concurrent_profiles_enqueue_one_shared_organization_call(self, dispatch):
        barrier = Barrier(2)

        def enqueue(analysis_id):
            close_old_connections()
            try:
                analysis = VacancyAnalysis.objects.select_related("profile", "vacancy", "matching_config").get(pk=analysis_id)
                barrier.wait(timeout=5)
                return queue_organization(analysis).pk
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as workers:
            organization_ids = list(workers.map(enqueue, self.analyses))

        self.assertEqual(organization_ids[0], organization_ids[1])
        self.assertEqual(VacancyOrganization.objects.count(), 1)
        dispatch.assert_called_once()
