from unittest.mock import patch
from dataclasses import replace

from django.contrib.auth import get_user_model
from django.test import TestCase

from dashboard.models import VacancyFollowUp
from jobs.models import ManualVacancySubmission, Vacancy
from matching.models import PROMPT_VERSION, RUBRIC_VERSION, MatchingConfig, VacancyAnalysis
from matching.tasks import schedule_vacancy_analysis
from jobs.tasks import process_manual_vacancy_submission
from jobs.connectors.base import JobListing
from jobs.connectors.elempleo import ElempleoConnector
from profiles.models import Profile, ProfileRevision
from profiles.locations import vacancy_location_is_eligible


class ManualVacancySubmissionTaskTests(TestCase):
    def setUp(self):
        self.fetch_patcher = patch.object(
            ElempleoConnector,
            "fetch_vacancy_url",
            return_value=JobListing(
                source="elempleo_co", external_id="123", title="Analista de procesos",
                company="Empresa de prueba", location="Medellín", description="Mejora de procesos.",
                original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-123",
                raw_data={"details": {"modality": "presencial"}}, salary="4 millones",
                contract_type="Indefinido",
            ),
        )
        self.fetch_mock = self.fetch_patcher.start()
        self.addCleanup(self.fetch_patcher.stop)

    def create_submission(self, **overrides):
        values = {
            "original_url": "https://www.elempleo.com/co/ofertas-trabajo/analista-123",
        }
        values.update(overrides)
        return ManualVacancySubmission.objects.create(**values)

    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    def test_new_submission_is_canonicalized_and_analysis_is_delegated_asynchronously(self, schedule):
        submission = self.create_submission(
            original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-123/?utm_source=test"
        )

        result = process_manual_vacancy_submission.run(submission.pk)

        submission.refresh_from_db()
        vacancy = Vacancy.objects.get()
        self.assertEqual(result["status"], ManualVacancySubmission.Status.SCHEDULED)
        self.assertEqual(vacancy.original_url, "https://www.elempleo.com/co/ofertas-trabajo/analista-123")
        self.assertEqual(submission.vacancy, vacancy)
        self.assertEqual(submission.status, ManualVacancySubmission.Status.SCHEDULED)
        self.assertIn("Vacante nueva guardada", submission.result_message)
        schedule.assert_called_once_with(vacancy.pk, force_reanalysis=True)

    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    def test_existing_canonical_url_is_updated_without_creating_another_vacancy(self, schedule):
        vacancy = Vacancy.objects.create(
            source="elempleo_co",
            title="Título anterior",
            company="Empresa de prueba",
            location="Medellín",
            description="Descripción anterior.",
            original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-123",
        )
        submission = self.create_submission(
            original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-123/?ref=manual",
        )

        process_manual_vacancy_submission.run(submission.pk)

        vacancy.refresh_from_db()
        submission.refresh_from_db()
        self.assertEqual(Vacancy.objects.count(), 1)
        self.assertEqual(submission.vacancy, vacancy)
        self.assertEqual(vacancy.title, "Analista de procesos")
        self.assertEqual(vacancy.original_url, "https://www.elempleo.com/co/ofertas-trabajo/analista-123")
        self.assertIn("actualizada", submission.result_message)
        schedule.assert_called_once_with(vacancy.pk, force_reanalysis=True)

    def test_duplicate_delivery_does_not_process_submission_twice(self):
        submission = self.create_submission()
        submission.status = ManualVacancySubmission.Status.SCHEDULED
        submission.save(update_fields=["status"])

        result = process_manual_vacancy_submission.run(submission.pk)

        self.assertEqual(result, {"skipped": "already_processed"})
        self.assertFalse(Vacancy.objects.exists())

    @patch(
        "matching.tasks.schedule_vacancy_analysis.delay",
        side_effect=RuntimeError("broker detail must not be stored"),
    )
    def test_failed_analysis_dispatch_is_recorded_without_exposing_exception(self, dispatch):
        submission = self.create_submission()

        result = process_manual_vacancy_submission.run(submission.pk)

        submission.refresh_from_db()
        self.assertEqual(result["status"], ManualVacancySubmission.Status.FAILED)
        self.assertEqual(submission.status, ManualVacancySubmission.Status.FAILED)
        self.assertIn("No fue posible guardar", submission.result_message)
        self.assertNotIn("broker detail", submission.result_message)
        self.assertEqual(Vacancy.objects.count(), 1)
        dispatch.assert_called_once()

    def make_profile(self, username, *, location, remote_ok=False, min_score=0):
        user = get_user_model().objects.create_user(username)
        profile = Profile.objects.create(
            owner=user,
            search_phrases=["Analista de procesos"],
            locations=[location],
            remote_ok=remote_ok,
            min_score=min_score,
            cv_file=f"profiles/{user.pk}/cv/v1.pdf",
            revision_number=1,
        )
        revision = ProfileRevision.objects.create(
            profile=profile,
            version=1,
            search_phrases=profile.search_phrases,
            locations=profile.locations,
            remote_ok=remote_ok,
            cv_file_path=profile.cv_file.name,
        )
        return profile, revision

    def make_matching_config(self):
        return MatchingConfig.objects.create(
            version=1,
            rubric_version=RUBRIC_VERSION,
            prompt_version=PROMPT_VERSION,
            analysis_prompt="Compara el perfil y la publicación.",
            organization_prompt="Resume la publicación.",
        )

    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    def test_manual_vacancy_only_creates_analyses_for_geographically_eligible_profiles(
        self, dispatch_manual, dispatch_analysis
    ):
        self.make_matching_config()
        eligible, _ = self.make_profile("medellin", location="Medellín")
        self.make_profile("bogota", location="Bogotá")
        submission = self.create_submission(location="Medellín", modality="presencial")

        process_manual_vacancy_submission.run(submission.pk)
        vacancy_id, options = dispatch_manual.call_args.args[0], dispatch_manual.call_args.kwargs
        with self.captureOnCommitCallbacks(execute=True):
            queued = schedule_vacancy_analysis.run(vacancy_id, **options)

        self.assertEqual(len(queued), 1)
        self.assertEqual(
            list(VacancyAnalysis.objects.filter(vacancy_id=vacancy_id).values_list("profile_id", flat=True)),
            [eligible.pk],
        )
        dispatch_analysis.assert_called_once()

    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    def test_remote_manual_vacancy_only_reaches_profiles_that_accept_remote(
        self, dispatch_manual, dispatch_analysis
    ):
        self.make_matching_config()
        self.make_profile("remote-disabled", location="Bogotá", remote_ok=False)
        remote_eligible, _ = self.make_profile("remote-enabled", location="Bogotá", remote_ok=True)
        self.fetch_mock.return_value = replace(
            self.fetch_mock.return_value,
            location="Remoto",
            raw_data={"details": {"modality": "remoto"}},
        )
        submission = self.create_submission(location="Remoto", modality="remoto")

        process_manual_vacancy_submission.run(submission.pk)
        vacancy_id, options = dispatch_manual.call_args.args[0], dispatch_manual.call_args.kwargs
        vacancy = Vacancy.objects.get(pk=vacancy_id)
        revision = remote_eligible.revisions.get(version=remote_eligible.revision_number)
        self.assertEqual((vacancy.raw_data.get("details") or {}).get("modality"), "remoto")
        self.assertTrue(vacancy_location_is_eligible(vacancy, revision))
        with self.captureOnCommitCallbacks(execute=True):
            queued = schedule_vacancy_analysis.run(vacancy_id, **options)

        self.assertEqual(len(queued), 1)
        self.assertEqual(
            list(VacancyAnalysis.objects.filter(vacancy_id=vacancy_id).values_list("profile_id", flat=True)),
            [remote_eligible.pk],
        )
        dispatch_analysis.assert_called_once()

    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    def test_unchanged_manual_resubmission_keeps_completed_analysis_and_follow_up(
        self, dispatch_manual, dispatch_analysis
    ):
        self.make_matching_config()
        profile, revision = self.make_profile("existing", location="Medellín")
        vacancy = Vacancy.objects.create(
            source="elempleo_co",
            title="Analista de procesos",
            company="Empresa de prueba",
            location="Medellín",
            description="Mejora de procesos.",
            salary="4 millones",
            contract_type="Indefinido",
            original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-123",
        )
        config = MatchingConfig.objects.get(is_active=True)
        VacancyAnalysis.objects.create(
            profile=profile,
            profile_revision=revision,
            vacancy=vacancy,
            matching_config=config,
            status=VacancyAnalysis.Status.COMPLETED,
            score="8.0",
        )
        follow_up = VacancyFollowUp.objects.create(
            profile=profile,
            vacancy=vacancy,
            status=VacancyFollowUp.Status.APPLIED,
        )
        self.fetch_mock.return_value = replace(self.fetch_mock.return_value, raw_data={})
        submission = self.create_submission(original_url=f"{vacancy.original_url}/?ref=manual")

        process_manual_vacancy_submission.run(submission.pk)
        vacancy_id, options = dispatch_manual.call_args.args[0], dispatch_manual.call_args.kwargs
        with self.captureOnCommitCallbacks(execute=True):
            queued = schedule_vacancy_analysis.run(vacancy_id, **options)

        self.assertEqual(queued, [])
        self.assertEqual(Vacancy.objects.count(), 1)
        self.assertEqual(VacancyAnalysis.objects.filter(vacancy=vacancy).count(), 1)
        follow_up.refresh_from_db()
        self.assertEqual(follow_up.status, VacancyFollowUp.Status.APPLIED)
        dispatch_analysis.assert_not_called()

    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    @patch("matching.tasks.schedule_vacancy_analysis.delay")
    def test_manual_fanout_keeps_each_profile_analysis_threshold_and_follow_up_independent(
        self, dispatch_manual, dispatch_analysis
    ):
        config = self.make_matching_config()
        first_profile, first_revision = self.make_profile(
            "first-eligible", location="Medellín", min_score=6,
        )
        second_profile, second_revision = self.make_profile(
            "second-eligible", location="Valle de Aburrá", min_score=4,
        )
        submission = self.create_submission(location="Medellín", modality="presencial")

        process_manual_vacancy_submission.run(submission.pk)
        vacancy_id, options = dispatch_manual.call_args.args[0], dispatch_manual.call_args.kwargs
        with self.captureOnCommitCallbacks(execute=True):
            queued = schedule_vacancy_analysis.run(vacancy_id, **options)

        analyses = list(VacancyAnalysis.objects.filter(vacancy_id=vacancy_id).order_by("profile_id"))
        self.assertEqual(len(queued), 2)
        self.assertEqual({analysis.profile_id for analysis in analyses}, {first_profile.pk, second_profile.pk})
        self.assertEqual(
            {analysis.profile_revision_id for analysis in analyses},
            {first_revision.pk, second_revision.pk},
        )
        self.assertEqual({analysis.matching_config_id for analysis in analyses}, {config.pk})
        thresholds = dict(
            first_profile.vacancy_discoveries.filter(vacancy_id=vacancy_id).values_list(
                "profile_id", "auto_discard_threshold",
            )
        )
        thresholds.update(
            second_profile.vacancy_discoveries.filter(vacancy_id=vacancy_id).values_list(
                "profile_id", "auto_discard_threshold",
            )
        )
        self.assertEqual(thresholds, {first_profile.pk: 6, second_profile.pk: 4})

        first_follow_up = VacancyFollowUp.objects.create(
            profile=first_profile,
            vacancy_id=vacancy_id,
            status=VacancyFollowUp.Status.APPLIED,
        )
        second_follow_up = VacancyFollowUp.objects.create(
            profile=second_profile,
            vacancy_id=vacancy_id,
            status=VacancyFollowUp.Status.PENDING,
        )
        first_follow_up.status = VacancyFollowUp.Status.INTERVIEW
        first_follow_up.save(update_fields=["status", "updated_at"])

        duplicate_submission = self.create_submission(
            original_url=f"{Vacancy.objects.get(pk=vacancy_id).original_url}/?campaign=manual"
        )
        process_manual_vacancy_submission.run(duplicate_submission.pk)
        duplicate_options = dispatch_manual.call_args.kwargs
        with self.captureOnCommitCallbacks(execute=True):
            duplicate_queued = schedule_vacancy_analysis.run(vacancy_id, **duplicate_options)

        self.assertEqual(duplicate_queued, [])
        self.assertEqual(Vacancy.objects.count(), 1)
        self.assertEqual(VacancyAnalysis.objects.filter(vacancy_id=vacancy_id).count(), 2)
        first_follow_up.refresh_from_db()
        second_follow_up.refresh_from_db()
        self.assertEqual(first_follow_up.status, VacancyFollowUp.Status.INTERVIEW)
        self.assertEqual(second_follow_up.status, VacancyFollowUp.Status.PENDING)
        self.assertEqual(dispatch_analysis.call_count, 2)
