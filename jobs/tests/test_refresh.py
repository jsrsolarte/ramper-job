from unittest.mock import Mock, call, patch

from celery.exceptions import Retry
from django.contrib.auth import get_user_model
from django.test import TestCase

from dashboard.models import VacancyFollowUp
from jobs.connectors.base import JobListing, SourceUnavailable
from jobs.models import JobSourceStatus, Vacancy
from jobs.tasks import refresh_profile_sources, refresh_shared_sources, refresh_sources
from matching.client import OmniRouteError
from matching.models import (
    PROMPT_VERSION,
    RUBRIC_VERSION,
    MatchingConfig,
    ProfileSearchTerms,
)
from matching.tasks import schedule_vacancy_analysis
from operations.models import AdminCommandRun, OperationalRun, RefreshLease
from operations.services import acquire_refresh_lease, start_admin_command
from profiles.models import Profile, ProfileRevision
from profiles.locations import MEDELLIN_AREA


def listing(title="Vacante de prueba", description="Descripción nueva", location="Cali", raw_data=None):
    return JobListing(
        source="test-source",
        external_id="123",
        title=title,
        company="Empresa",
        location=location,
        description=description,
        original_url="https://jobs.example.test/vacancy/123",
        raw_data=raw_data or {},
    )


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

    def _staged_connector(self):
        class StagedConnector:
            source = "test-source"
            status_message = ""

            def __init__(self):
                self.detail_inputs = []
                self.cards = [
                    listing("Auxiliar de cocina", location="Medellín"),
                    listing("Analista de procesos", location="Medellín"),
                ]

            def fetch_titles(self, keywords, locations=None, *, remote_ok=False):
                self.search = (keywords, locations, remote_ok)
                return self.cards

            def fetch_details(self, selected):
                self.detail_inputs = list(selected)
                return list(selected)

            def fetch(self, *args, **kwargs):
                raise AssertionError("El conector escalonado no debe usar fetch completo")

        return StagedConnector()

    @patch("matching.services.request_model_title_preselection")
    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    @patch("jobs.tasks.configured_connectors")
    def test_profile_refresh_filters_titles_before_detail_fetch(self, configured, schedule_analysis, preselect):
        connector = self._staged_connector()
        configured.return_value = [connector]
        preselect.return_value = Mock(
            content={"decisions": [{"id": "0", "keep": False}, {"id": "1", "keep": True}]},
            input_tokens=18,
        )

        with self.captureOnCommitCallbacks(execute=True):
            refresh_profile_sources.run(self.profile.pk)

        self.assertEqual([item.title for item in connector.detail_inputs], ["Analista de procesos"])
        self.assertEqual(Vacancy.objects.count(), 1)
        schedule_analysis.assert_called_once()
        preselect.assert_called_once_with(
            search_terms=self.term_set.keywords,
            vacancies=[
                {"id": "0", "title": "Auxiliar de cocina"},
                {"id": "1", "title": "Analista de procesos"},
            ],
        )

    @patch("matching.services.request_model_title_preselection")
    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    @patch("jobs.tasks.configured_connectors")
    def test_shared_refresh_preselects_once_and_fans_out_to_equivalent_profiles(
        self, configured, schedule_analysis, preselect,
    ):
        other_user = get_user_model().objects.create_user("member2")
        other_profile = Profile.objects.create(
            owner=other_user,
            search_phrases=["Analista de procesos"],
            locations=["Medellín"],
            cv_file="profiles/2/cv/v1.pdf",
            revision_number=1,
        )
        other_revision = ProfileRevision.objects.create(
            profile=other_profile,
            version=1,
            search_phrases=other_profile.search_phrases,
            locations=other_profile.locations,
            cv_file_path=other_profile.cv_file.name,
        )
        ProfileSearchTerms.objects.create(
            profile_revision=other_revision,
            matching_config=self.config,
            keywords=self.term_set.keywords,
        )
        connector = self._staged_connector()
        configured.return_value = [connector]
        preselect.return_value = Mock(
            content={"decisions": [{"id": "0", "keep": False}, {"id": "1", "keep": True}]},
            input_tokens=18,
        )
        leases = {
            str(profile.pk): acquire_refresh_lease(f"profile-refresh:{profile.pk}")
            for profile in (self.profile, other_profile)
        }

        with self.captureOnCommitCallbacks(execute=True):
            refresh_shared_sources.run(leases)

        self.assertEqual(connector.search[0], self.term_set.keywords)
        self.assertEqual([item.title for item in connector.detail_inputs], ["Analista de procesos"])
        self.assertEqual(Vacancy.objects.count(), 1)
        preselect.assert_called_once()
        schedule_analysis.assert_called_once()
        self.assertCountEqual(
            schedule_analysis.call_args.kwargs["profile_ids"], [self.profile.pk, other_profile.pk],
        )

    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    @patch("jobs.tasks.configured_connectors")
    def test_refresh_saves_new_vacancy_updates_duplicate_and_passes_terms(self, configured, schedule_analysis):
        connector = Mock(source="test-source", status_message="")
        connector.fetch.side_effect = [
            [listing()],
            [listing(title="Título actualizado", description="Descripción actualizada")],
        ]
        configured.return_value = [connector]

        with self.captureOnCommitCallbacks(execute=True):
            refresh_profile_sources.run(self.profile.pk)
            refresh_profile_sources.run(self.profile.pk)

        self.assertEqual(Vacancy.objects.count(), 1)
        vacancy = Vacancy.objects.get()
        self.assertEqual(vacancy.title, "Título actualizado")
        self.assertEqual(vacancy.description, "Descripción actualizada")
        self.assertEqual(JobSourceStatus.objects.get().last_vacancy_count, 1)
        connector.fetch.assert_has_calls([
            call(self.term_set.keywords, locations=list(MEDELLIN_AREA), remote_ok=False),
            call(self.term_set.keywords, locations=list(MEDELLIN_AREA), remote_ok=False),
        ])
        self.assertEqual(schedule_analysis.call_count, 2)
        self.assertEqual(schedule_analysis.call_args.kwargs, {"force_reanalysis": True})
        self.assertEqual(
            OperationalRun.objects.filter(
                operation="source_query", status=OperationalRun.Status.SUCCEEDED
            ).count(),
            2,
        )
        query_runs = list(OperationalRun.objects.filter(
            operation="source_query", status=OperationalRun.Status.SUCCEEDED,
        ).order_by("pk"))
        self.assertEqual(
            [(run.item_count, run.new_count, run.known_count,
              run.known_updated_count, run.known_unchanged_count) for run in query_runs],
            [(1, 1, 0, 0, 0), (1, 0, 1, 1, 0)],
        )

    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    @patch("jobs.tasks.configured_connectors")
    def test_reingesting_updated_vacancy_preserves_discarded_profile_follow_up(self, configured, schedule_analysis):
        connector = Mock(source="test-source", status_message="")
        connector.fetch.side_effect = [
            [listing()],
            [listing(title="Vacante actualizada", description="Descripción actualizada")],
        ]
        configured.return_value = [connector]

        with self.captureOnCommitCallbacks(execute=True):
            refresh_profile_sources.run(self.profile.pk)
        vacancy = Vacancy.objects.get()
        follow_up = VacancyFollowUp.objects.create(
            profile=self.profile,
            vacancy=vacancy,
            status=VacancyFollowUp.Status.DISCARDED,
            previous_status=VacancyFollowUp.Status.PENDING,
        )

        with self.captureOnCommitCallbacks(execute=True):
            refresh_profile_sources.run(self.profile.pk)

        follow_up.refresh_from_db()
        self.assertEqual(Vacancy.objects.count(), 1)
        self.assertEqual(follow_up.status, VacancyFollowUp.Status.DISCARDED)
        self.assertEqual(VacancyFollowUp.objects.filter(profile=self.profile, vacancy=vacancy).count(), 1)
        schedule_analysis.assert_called_with(vacancy.pk, force_reanalysis=True)

    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    @patch("jobs.tasks.configured_connectors")
    def test_unchanged_vacancy_does_not_schedule_another_model_analysis(self, configured, schedule_analysis):
        connector = Mock(source="test-source", status_message="")
        connector.fetch.return_value = [listing()]
        configured.return_value = [connector]

        with self.captureOnCommitCallbacks(execute=True):
            refresh_profile_sources.run(self.profile.pk)
            refresh_profile_sources.run(self.profile.pk)

        self.assertEqual(Vacancy.objects.count(), 1)
        schedule_analysis.assert_called_once()

    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    @patch("jobs.tasks.configured_connectors")
    def test_partial_success_is_recorded_on_source_status(self, configured, schedule_analysis):
        connector = Mock(source="test-source", status_message="HTTP 503 para procesos")
        connector.fetch.return_value = [listing()]
        configured.return_value = [connector]

        refresh_profile_sources.run(self.profile.pk)

        status = JobSourceStatus.objects.get(source="test-source")
        self.assertTrue(status.available)
        self.assertIn("HTTP 503", status.status_message)
        self.assertEqual(status.last_vacancy_count, 1)

    @patch("jobs.tasks.configured_connectors")
    def test_source_failure_is_recorded_for_dashboard(self, configured):
        connector = Mock(source="test-source", fetch=Mock(side_effect=SourceUnavailable("Consulta no permitida")))
        configured.return_value = [connector]

        result = refresh_profile_sources.run(self.profile.pk)

        status = JobSourceStatus.objects.get(source="test-source")
        self.assertFalse(status.available)
        self.assertIn("Consulta no permitida", status.status_message)
        self.assertIsNotNone(status.last_checked_at)
        self.assertEqual(result[0]["available"], False)
        run = OperationalRun.objects.get(operation="source_query")
        self.assertEqual(run.status, OperationalRun.Status.FAILED)
        self.assertEqual(run.error_category, "source_unavailable")
        self.assertNotIn("Consulta no permitida", run.error_summary)
        self.assertIsNone(run.new_count)
        self.assertIsNone(run.known_count)

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
            search_phrases=["Ingeniero de procesos"],
            locations=["Bogotá"],
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
    def test_manual_refresh_dispatches_batch_with_audit_id(self, refresh_shared):
        command = AdminCommandRun.objects.create(command="refresh_sources", requested_by=self.profile.owner)

        result = refresh_sources.run(command.pk)

        command.refresh_from_db()
        self.assertEqual(result, {"scheduled_profiles": 1})
        self.assertEqual(command.status, AdminCommandRun.Status.RUNNING)
        self.assertEqual(command.profile_count, 1)
        refresh_shared.assert_called_once()
        self.assertEqual(refresh_shared.call_args.kwargs["command_run_id"], command.pk)
        leases = refresh_shared.call_args.args[0]
        self.assertEqual(set(leases), {str(self.profile.pk)})
        self.assertTrue(RefreshLease.objects.filter(token=leases[str(self.profile.pk)]).exists())

    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    @patch("jobs.tasks.configured_connectors")
    @patch("jobs.tasks.refresh_shared_sources.delay")
    def test_manual_command_completes_normal_ingestion_without_duplicate_vacancy_or_analysis(
        self, refresh_shared, configured, schedule_analysis,
    ):
        command = AdminCommandRun.objects.create(command="refresh_sources", requested_by=self.profile.owner)
        connector = Mock(source="test-source", status_message="")
        connector.fetch.return_value = [listing(location="Medellín")]
        configured.return_value = [connector]

        self.assertEqual(refresh_sources.run(command.pk), {"scheduled_profiles": 1})
        leases = refresh_shared.call_args.args[0]
        with self.captureOnCommitCallbacks(execute=True):
            refresh_shared_sources.run(leases, **refresh_shared.call_args.kwargs)
            refresh_shared_sources.run(leases, **refresh_shared.call_args.kwargs)

        command.refresh_from_db()
        self.assertEqual(command.status, AdminCommandRun.Status.SUCCEEDED)
        self.assertEqual(command.source_results["test-source"]["queries"], 1)
        self.assertEqual(Vacancy.objects.count(), 1)
        schedule_analysis.assert_called_once()

    @patch("jobs.tasks.configured_connectors")
    def test_profile_refresh_records_safe_source_summary_and_releases_shared_lease(self, configured):
        command = AdminCommandRun.objects.create(command="refresh_sources", requested_by=self.profile.owner)
        start_admin_command(command.pk, 1)
        connector = Mock(source="test-source", status_message="")
        connector.fetch.return_value = [listing()]
        configured.return_value = [connector]

        result = refresh_profile_sources.run(self.profile.pk, command_run_id=command.pk)

        command.refresh_from_db()
        self.assertEqual(result[0]["count"], 1)
        self.assertEqual(command.status, AdminCommandRun.Status.SUCCEEDED)
        self.assertEqual(command.source_results["test-source"]["vacancies"], 1)
        self.assertFalse(RefreshLease.objects.exists())

    @patch("jobs.tasks.configured_connectors")
    def test_profile_refresh_skips_work_when_scheduled_and_manual_runs_overlap(self, configured):
        command = AdminCommandRun.objects.create(command="refresh_sources", requested_by=self.profile.owner)
        start_admin_command(command.pk, 1)
        token = acquire_refresh_lease(f"profile-refresh:{self.profile.pk}")

        result = refresh_profile_sources.run(self.profile.pk, command_run_id=command.pk)

        configured.assert_not_called()
        self.assertEqual(result, {"skipped": "already_running"})
        self.assertEqual(command.__class__.objects.get(pk=command.pk).status, AdminCommandRun.Status.SUCCEEDED)
        self.assertTrue(RefreshLease.objects.filter(token=token).exists())

    @patch("matching.services.request_model_keywords", side_effect=OmniRouteError("OmniRoute caído"))
    @patch("matching.services.extract_revision_text", return_value="CV actualizado")
    def test_keyword_service_failure_retries_without_general_search(self, extract, request):
        self.profile.revision_number = 2
        self.profile.save(update_fields=["revision_number"])
        ProfileRevision.objects.create(
            profile=self.profile,
            version=2,
            search_phrases=["Otro perfil"],
            locations=["Medellín"],
            cv_file_path=self.profile.cv_file.name,
        )
        existing = Vacancy.objects.create(
            source="test-source",
            title="Guardada antes",
            original_url="https://jobs.example.test/vacancy/old",
        )

        with patch.object(refresh_profile_sources, "retry") as retry, patch(
            "jobs.tasks.configured_connectors"
        ) as configured:
            retry.side_effect = Retry()
            with self.assertRaises(Retry):
                refresh_profile_sources.run(self.profile.pk)

        self.assertTrue(Vacancy.objects.filter(pk=existing.pk).exists())
        request.assert_called_once()
        configured.assert_not_called()
        retry.assert_called_once()

    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    @patch("jobs.tasks.refresh_shared_sources.delay")
    @patch("jobs.tasks.configured_connectors")
    def test_distinct_searches_dedupe_one_vacancy_and_fan_out_to_both_profiles(
        self, configured, refresh_shared, schedule_analysis
    ):
        other_user = get_user_model().objects.create_user("member2")
        other_profile = Profile.objects.create(
            owner=other_user,
            search_phrases=["Ingeniero de automatización"],
            locations=["Medellín"],
            cv_file="profiles/2/cv/v1.pdf",
            revision_number=1,
        )
        other_revision = ProfileRevision.objects.create(
            profile=other_profile,
            version=1,
            search_phrases=["Ingeniero de automatización"],
            locations=["Medellín"],
            cv_file_path=other_profile.cv_file.name,
        )
        ProfileSearchTerms.objects.create(
            profile_revision=other_revision,
            matching_config=self.config,
            keywords=["automatización", "ingeniero de procesos"],
        )
        connector = Mock(source="test-source", status_message="")
        connector.fetch.return_value = [listing(location="Medellín")]
        configured.return_value = [connector]
        result = refresh_sources.run()

        self.assertEqual(result["scheduled_profiles"], 2)
        leases = refresh_shared.call_args.args[0]
        with self.captureOnCommitCallbacks(execute=True):
            refresh_shared_sources.run(leases)

        connector.fetch.assert_has_calls([
            call(self.term_set.keywords, locations=list(MEDELLIN_AREA), remote_ok=False),
            call(["automatización", "ingeniero de procesos"], locations=list(MEDELLIN_AREA), remote_ok=False),
        ])
        self.assertEqual(Vacancy.objects.count(), 1)
        vacancy = Vacancy.objects.get()
        schedule_analysis.assert_called_once()
        kwargs = schedule_analysis.call_args.kwargs
        self.assertCountEqual(kwargs["profile_ids"], [self.profile.pk, other_profile.pk])
        self.assertEqual(Vacancy.objects.filter(source="test-source").count(), 1)
        self.assertEqual(JobSourceStatus.objects.get().last_vacancy_count, 1)
        query_runs = list(OperationalRun.objects.filter(
            operation="source_query", status=OperationalRun.Status.SUCCEEDED,
        ))
        self.assertEqual(len(query_runs), 2)
        self.assertEqual(sum(run.item_count for run in query_runs), 2)
        self.assertEqual(sum(run.new_count for run in query_runs), 1)
        self.assertEqual(sum(run.known_count for run in query_runs), 1)

    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    @patch("jobs.tasks.refresh_shared_sources.delay")
    @patch("jobs.tasks.configured_connectors")
    def test_equivalent_profiles_share_one_query_and_fan_out_idempotently(
        self, configured, refresh_shared, schedule_analysis, analyze_profile,
    ):
        other_user = get_user_model().objects.create_user("member2")
        other_profile = Profile.objects.create(
            owner=other_user,
            search_phrases=["analista de procesos"],
            locations=["Medellín"],
            cv_file="profiles/2/cv/v1.pdf",
            revision_number=1,
        )
        other_revision = ProfileRevision.objects.create(
            profile=other_profile,
            version=1,
            search_phrases=["analista de procesos"],
            locations=["Medellín"],
            cv_file_path=other_profile.cv_file.name,
        )
        ProfileSearchTerms.objects.create(
            profile_revision=other_revision,
            matching_config=self.config,
            keywords=["Procesos", "  analista   de procesos "],
        )
        connector = Mock(source="test-source", status_message="")
        connector.fetch.return_value = [listing(location="Medellín")]
        configured.return_value = [connector]

        self.assertEqual(refresh_sources.run()["scheduled_profiles"], 2)
        leases = refresh_shared.call_args.args[0]
        with self.captureOnCommitCallbacks(execute=True):
            refresh_shared_sources.run(leases)

        connector.fetch.assert_called_once_with(
            self.term_set.keywords,
            locations=list(MEDELLIN_AREA),
            remote_ok=False,
        )
        self.assertEqual(Vacancy.objects.count(), 1)
        schedule_analysis.assert_called_once()
        args = schedule_analysis.call_args.args
        kwargs = schedule_analysis.call_args.kwargs
        with self.captureOnCommitCallbacks(execute=True):
            first = schedule_vacancy_analysis.run(*args, **kwargs)
            second = schedule_vacancy_analysis.run(*args, **kwargs)
        self.assertEqual(len(first), 2)
        self.assertEqual(second, [])
        self.assertEqual(Vacancy.objects.first().analyses.count(), 2)
        self.assertEqual(analyze_profile.call_count, 2)

        vacancy = Vacancy.objects.first()
        first_follow_up = VacancyFollowUp.objects.create(
            profile=self.profile,
            vacancy=vacancy,
            status=VacancyFollowUp.Status.APPLIED,
        )
        other_follow_up = VacancyFollowUp.objects.create(
            profile=other_profile,
            vacancy=vacancy,
            status=VacancyFollowUp.Status.PENDING,
        )
        first_follow_up.status = VacancyFollowUp.Status.INTERVIEW
        first_follow_up.save(update_fields=["status", "updated_at"])
        other_follow_up.refresh_from_db()
        self.assertEqual(first_follow_up.status, VacancyFollowUp.Status.INTERVIEW)
        self.assertEqual(other_follow_up.status, VacancyFollowUp.Status.PENDING)

    @patch("jobs.tasks.refresh_profile_sources.delay")
    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    @patch("jobs.tasks.configured_connectors")
    def test_profile_changed_during_shared_query_is_not_associated(self, configured, schedule_analysis, refresh_profile):
        connector = Mock(source="test-source", status_message="")

        def fetch(*args, **kwargs):
            new_revision = ProfileRevision.objects.create(
                profile=self.profile,
                version=2,
                search_phrases=["Otro cargo"],
                locations=["Medellín"],
                cv_file_path=self.profile.cv_file.name,
            )
            Profile.objects.filter(pk=self.profile.pk).update(revision_number=new_revision.version)
            return [listing(location="Medellín")]

        connector.fetch.side_effect = fetch
        configured.return_value = [connector]
        token = acquire_refresh_lease(f"profile-refresh:{self.profile.pk}")

        result = refresh_shared_sources.run({str(self.profile.pk): token})

        self.assertEqual(result["refreshed_profiles"], 1)
        self.assertEqual(Vacancy.objects.count(), 1)
        schedule_analysis.assert_not_called()
        refresh_profile.assert_called_once_with(self.profile.pk, command_run_id=None)
