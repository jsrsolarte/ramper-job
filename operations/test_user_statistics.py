from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dashboard.models import VacancyFollowUp
from jobs.models import Vacancy
from matching.models import MatchingConfig, ProfileVacancyDiscovery, RUBRIC_VERSION, VacancyAnalysis
from operations.user_statistics import build_applicant_statistics
from profiles.models import Profile, ProfileRevision


class ApplicantStatisticsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser("owner", password="strong-admin-pass")
        self.applicant = User.objects.create_user("candidate", password="strong-applicant-pass")
        self.other_applicant = User.objects.create_user("other", password="another-applicant-pass")
        self.profile = Profile.objects.create(owner=self.applicant, revision_number=1, min_score=10)
        self.revision = ProfileRevision.objects.create(profile=self.profile, version=1)
        self.other_profile = Profile.objects.create(owner=self.other_applicant, revision_number=1)
        self.other_revision = ProfileRevision.objects.create(profile=self.other_profile, version=1)
        self.config = MatchingConfig.objects.create(
            version=1,
            rubric_version=RUBRIC_VERSION,
            analysis_prompt="Prompt",
            organization_prompt="Organiza",
        )
        self.client.force_login(self.admin)

    def _analysis(self, profile, revision, *, title, status, score=None, completed_at=None):
        vacancy = Vacancy.objects.create(
            source="elempleo_co",
            title=title,
            original_url=f"https://jobs.example.test/{title.lower().replace(' ', '-')}",
        )
        analysis = VacancyAnalysis.objects.create(
            profile=profile,
            profile_revision=revision,
            vacancy=vacancy,
            matching_config=self.config,
            status=status,
            score=Decimal(str(score)) if score is not None else None,
            score_breakdown={"skills": {"score": 1}} if status == VacancyAnalysis.Status.COMPLETED else {},
            completed_at=completed_at,
        )
        return analysis

    def test_dashboard_follow_up_semantics_include_implicit_pending_and_exclude_archived(self):
        statuses = [status for status, _label in VacancyFollowUp.Status.choices]
        for index, status in enumerate(statuses):
            analysis = self._analysis(
                self.profile,
                self.revision,
                title=f"Estado {index}",
                status=VacancyAnalysis.Status.COMPLETED,
                score=2,
            )
            VacancyFollowUp.objects.create(
                profile=self.profile,
                vacancy=analysis.vacancy,
                status=status,
            )

        implicit_pending = self._analysis(
            self.profile,
            self.revision,
            title="Pendiente implicita",
            status=VacancyAnalysis.Status.COMPLETED,
            score=2,
        )
        archived = self._analysis(
            self.profile,
            self.revision,
            title="Archivada",
            status=VacancyAnalysis.Status.COMPLETED,
            score=10,
        )
        VacancyFollowUp.objects.create(
            profile=self.profile,
            vacancy=archived.vacancy,
            status=VacancyFollowUp.Status.APPLIED,
            archived_at=timezone.now(),
        )
        other = self._analysis(
            self.other_profile,
            self.other_revision,
            title="Privada de otro perfil",
            status=VacancyAnalysis.Status.COMPLETED,
            score=10,
        )
        VacancyFollowUp.objects.create(
            profile=self.other_profile,
            vacancy=other.vacancy,
            status=VacancyFollowUp.Status.APPLIED,
        )

        statistics = build_applicant_statistics(self.profile)
        counts = {item["value"]: item["count"] for item in statistics["follow_up_states"]}

        self.assertEqual(counts[VacancyFollowUp.Status.PENDING], 2)
        self.assertEqual(counts[VacancyFollowUp.Status.APPLIED], 1)
        self.assertEqual(statistics["follow_up_total"], len(statuses) + 1)
        self.assertEqual(statistics["archived_count"], 1)
        self.assertNotIn(other.vacancy.title, str(statistics))

    def test_tracking_counts_ignore_profile_score_threshold_and_historical_date_range(self):
        completed = self._analysis(
            self.profile,
            self.revision,
            title="Puntaje bajo el minimo",
            status=VacancyAnalysis.Status.COMPLETED,
            score=2,
        )
        ProfileVacancyDiscovery.objects.create(
            profile=self.profile,
            vacancy=completed.vacancy,
            first_found_at=timezone.now() - timedelta(days=500),
        )

        statistics = build_applicant_statistics(self.profile)

        self.assertEqual(statistics["follow_up_total"], 1)
        self.assertEqual(statistics["follow_up_states"][0]["count"], 1)
        self.assertEqual(statistics["discovered_count"], 1)

    def test_analysis_status_counts_use_one_latest_result_per_vacancy_and_revision(self):
        old = self._analysis(
            self.profile,
            self.revision,
            title="Reanalizada",
            status=VacancyAnalysis.Status.COMPLETED,
            score=8,
            completed_at=timezone.now() - timedelta(days=10),
        )
        latest = VacancyAnalysis.objects.create(
            profile=self.profile,
            profile_revision=self.revision,
            vacancy=old.vacancy,
            matching_config=self.config,
            status=VacancyAnalysis.Status.PENDING,
        )
        failed = self._analysis(
            self.profile,
            self.revision,
            title="Error vigente",
            status=VacancyAnalysis.Status.FAILED,
        )
        completed = self._analysis(
            self.profile,
            self.revision,
            title="Completa vigente",
            status=VacancyAnalysis.Status.COMPLETED,
            score=6,
            completed_at=timezone.now(),
        )
        statistics = build_applicant_statistics(self.profile)

        self.assertEqual(latest.status, VacancyAnalysis.Status.PENDING)
        self.assertEqual(statistics["analysis_counts"], {
            VacancyAnalysis.Status.PENDING: 1,
            VacancyAnalysis.Status.COMPLETED: 1,
            VacancyAnalysis.Status.FAILED: 1,
        })
        self.assertEqual(statistics["historical_completed_count"], 2)
        self.assertEqual(statistics["latest_historical_completion"], completed.completed_at)
        self.assertEqual(failed.status, VacancyAnalysis.Status.FAILED)

    def test_current_analysis_counts_exclude_previous_profile_revisions(self):
        old_revision_analysis = self._analysis(
            self.profile,
            self.revision,
            title="Revision anterior",
            status=VacancyAnalysis.Status.COMPLETED,
            score=8,
            completed_at=timezone.now() - timedelta(days=30),
        )
        current_revision = ProfileRevision.objects.create(profile=self.profile, version=2)
        self.profile.revision_number = 2
        self.profile.save(update_fields=("revision_number",))
        current_analysis = self._analysis(
            self.profile,
            current_revision,
            title="Revision actual",
            status=VacancyAnalysis.Status.FAILED,
        )

        statistics = build_applicant_statistics(self.profile)

        self.assertEqual(statistics["analysis_counts"], {
            VacancyAnalysis.Status.PENDING: 0,
            VacancyAnalysis.Status.COMPLETED: 0,
            VacancyAnalysis.Status.FAILED: 1,
        })
        self.assertEqual(statistics["historical_completed_count"], 1)
        self.assertEqual(statistics["latest_historical_completion"], old_revision_analysis.completed_at)
        self.assertEqual(current_analysis.status, VacancyAnalysis.Status.FAILED)

    def test_history_is_per_profile_unique_by_discovery_and_uses_recorded_dates(self):
        first = self._analysis(
            self.profile,
            self.revision,
            title="Primera",
            status=VacancyAnalysis.Status.COMPLETED,
            score=6,
        )
        second = self._analysis(
            self.profile,
            self.revision,
            title="Segunda",
            status=VacancyAnalysis.Status.FAILED,
        )
        old_date = timezone.now() - timedelta(days=12)
        new_date = timezone.now() - timedelta(days=2)
        ProfileVacancyDiscovery.objects.create(
            profile=self.profile, vacancy=first.vacancy, first_found_at=old_date,
        )
        ProfileVacancyDiscovery.objects.create(
            profile=self.profile, vacancy=second.vacancy, first_found_at=new_date,
        )
        ProfileVacancyDiscovery.objects.create(
            profile=self.other_profile, vacancy=first.vacancy,
        )

        statistics = build_applicant_statistics(self.profile)

        self.assertEqual(statistics["discovered_count"], 2)
        self.assertEqual(statistics["latest_discovery"], new_date)
        self.assertEqual(statistics["historical_completed_count"], 1)
        self.assertEqual(statistics["latest_historical_completion"], first.completed_at)


class ApplicantStatisticsViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser("owner", password="strong-admin-pass")
        self.applicant = User.objects.create_user("candidate", password="strong-applicant-pass")
        self.inactive = User.objects.create_user("inactive", password="strong-applicant-pass", is_active=False)
        self.other_admin = User.objects.create_user(
            "staff-admin", password="strong-admin-pass", is_staff=True,
        )

    def test_admin_can_open_active_account_and_users_list_links_to_its_statistics(self):
        self.client.force_login(self.admin)

        listing = self.client.get(reverse("operations:users"))
        response = self.client.get(reverse("operations:applicant_statistics", args=[self.applicant.pk]))

        self.assertContains(listing, reverse("operations:applicant_statistics", args=[self.applicant.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "candidate")
        self.assertContains(response, "Perfil no configurado")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["Referrer-Policy"], "no-referrer")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_empty_profile_statistics_show_zeros_and_no_invented_dates(self):
        profile = Profile.objects.create(owner=self.applicant)
        self.client.force_login(self.admin)

        response = self.client.get(reverse("operations:applicant_statistics", args=[self.applicant.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["statistics"]["follow_up_total"], 0)
        self.assertEqual(response.context["statistics"]["analysis_total"], 0)
        self.assertEqual(response.context["statistics"]["latest_discovery"], None)
        self.assertEqual(response.context["statistics"]["latest_historical_completion"], None)
        self.assertContains(response, "Fecha no disponible")
        self.assertEqual(profile.owner, self.applicant)

    def test_statistics_page_explains_units_and_coverage_without_private_content(self):
        profile = Profile.objects.create(
            owner=self.applicant,
            revision_number=1,
            cv_file="profiles/private/candidate-cv.pdf",
        )
        revision = ProfileRevision.objects.create(profile=profile, version=1)
        config = MatchingConfig.objects.create(
            version=1,
            rubric_version=RUBRIC_VERSION,
            analysis_prompt="Prompt privado",
            organization_prompt="Organización privada",
        )
        vacancy = Vacancy.objects.create(
            source="elempleo_co",
            title="Vacante privada que no se debe mostrar",
            original_url="https://jobs.example.test/private-statistics",
        )
        analysis = VacancyAnalysis.objects.create(
            profile=profile,
            profile_revision=revision,
            vacancy=vacancy,
            matching_config=config,
            status=VacancyAnalysis.Status.COMPLETED,
            score=Decimal("4"),
            score_breakdown={"skills": {"score": 1}},
            error_message="Mensaje técnico privado",
            completed_at=timezone.now(),
        )
        VacancyFollowUp.objects.create(
            profile=profile,
            vacancy=vacancy,
            status=VacancyFollowUp.Status.APPLIED,
        )
        ProfileVacancyDiscovery.objects.create(profile=profile, vacancy=vacancy)
        self.client.force_login(self.admin)

        response = self.client.get(reverse("operations:applicant_statistics", args=[self.applicant.pk]))
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Estados actuales de vacantes")
        self.assertContains(response, "Pendiente de decisión")
        self.assertContains(response, "Seguimientos archivados por inactividad")
        self.assertContains(response, "Análisis vigentes de la revisión actual, máximo uno por vacante")
        self.assertContains(response, "Análisis completados conservados")
        self.assertContains(response, "No hay una cronología completa de cambios de seguimiento")
        self.assertIn("<time datetime=", content)
        self.assertNotIn(profile.cv_file.name, content)
        self.assertNotIn(vacancy.title, content)
        self.assertNotIn(analysis.error_message, content)
        self.assertNotIn(config.analysis_prompt, content)

    def test_unavailable_accounts_share_a_generic_not_found_response(self):
        self.client.force_login(self.admin)
        for user_id in (999999, self.inactive.pk, self.admin.pk, self.other_admin.pk):
            with self.subTest(user_id=user_id):
                response = self.client.get(reverse("operations:applicant_statistics", args=[user_id]))
                self.assertEqual(response.status_code, 404)
                self.assertContains(response, "La cuenta solicitada no está disponible", status_code=404)
                self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_non_admin_and_logged_out_users_cannot_retrieve_statistics(self):
        url = reverse("operations:applicant_statistics", args=[self.applicant.pk])
        self.client.force_login(self.applicant)
        self.assertEqual(self.client.get(url).status_code, 403)

        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("estadisticas-individuales", response.get("Location", ""))
