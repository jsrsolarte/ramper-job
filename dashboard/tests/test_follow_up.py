from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from dashboard.models import VacancyFollowUp
from jobs.models import Vacancy
from matching.models import RUBRIC_VERSION, MatchingConfig, VacancyAnalysis
from profiles.models import Profile


class VacancyFollowUpModelTests(TestCase):
    def setUp(self):
        self.profile = Profile.objects.create(owner=get_user_model().objects.create_user("follow-up"))
        self.vacancy = Vacancy.objects.create(
            source="elempleo_co",
            title="Analista de procesos",
            original_url="https://jobs.example.test/follow-up",
        )

    def test_new_follow_up_defaults_to_pending_decision(self):
        follow_up = VacancyFollowUp.objects.create(profile=self.profile, vacancy=self.vacancy)

        self.assertEqual(follow_up.status, VacancyFollowUp.Status.PENDING)
        self.assertEqual(follow_up.previous_status, VacancyFollowUp.Status.PENDING)

    def test_profile_and_vacancy_pair_is_unique(self):
        VacancyFollowUp.objects.create(profile=self.profile, vacancy=self.vacancy)

        with self.assertRaises(IntegrityError):
            VacancyFollowUp.objects.create(profile=self.profile, vacancy=self.vacancy)


class VacancyFollowUpActionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("follow-up-owner", password="pass")
        self.other_user = user_model.objects.create_user("follow-up-other", password="pass")
        self.profile = Profile.objects.create(
            owner=self.user, revision_number=1, cv_file="profiles/1/cv/v1.pdf"
        )
        self.other_profile = Profile.objects.create(
            owner=self.other_user, revision_number=1, cv_file="profiles/other/cv/v1.pdf"
        )
        self.revision = self.profile.revisions.create(version=1)
        self.other_revision = self.other_profile.revisions.create(version=1)
        self.config = MatchingConfig.objects.create(
            version=1, rubric_version=RUBRIC_VERSION, analysis_prompt="Prompt", organization_prompt="Organiza"
        )
        self.vacancy = Vacancy.objects.create(
            source="elempleo_co",
            title="Analista de procesos",
            original_url="https://jobs.example.test/follow-up-action",
        )
        self.analysis = VacancyAnalysis.objects.create(
            profile=self.profile,
            profile_revision=self.revision,
            vacancy=self.vacancy,
            matching_config=self.config,
            status=VacancyAnalysis.Status.COMPLETED,
            score=8,
            score_breakdown={"skills": {"score": 4}},
        )

    def test_update_requires_authentication(self):
        response = self.client.post(
            reverse("dashboard:update_follow_up", args=[self.vacancy.pk]), {"status": "applied"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_recommendation_card_offers_follow_up_states(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard:home"))

        self.assertContains(response, 'value="applied"')
        self.assertContains(response, "Marcar como aplicada")
        self.assertContains(response, "Descartar vacante")
        self.assertNotContains(response, 'value="interview"')

    def test_only_next_stage_actions_and_finalization_are_offered(self):
        self.client.force_login(self.user)
        applied = VacancyFollowUp.objects.create(
            profile=self.profile, vacancy=self.vacancy, status=VacancyFollowUp.Status.APPLIED
        )

        response = self.client.get(reverse("dashboard:home"), {"state": "applied"})

        self.assertContains(response, 'value="in_progress"')
        self.assertContains(response, 'value="finalized"')
        self.assertNotContains(response, 'value="interview"')
        self.assertNotContains(response, 'value="pending"')

        applied.status = VacancyFollowUp.Status.INTERVIEW
        applied.save(update_fields=["status"])
        response = self.client.get(reverse("dashboard:home"), {"state": "interview"})
        self.assertContains(response, 'value="finalized"')
        self.assertNotContains(response, 'value="in_progress"')

    def test_recommendations_are_default_and_other_tabs_filter_by_profile_state(self):
        VacancyFollowUp.objects.create(
            profile=self.profile, vacancy=self.vacancy, status=VacancyFollowUp.Status.APPLIED
        )
        self.client.force_login(self.user)

        default_response = self.client.get(reverse("dashboard:home"))
        applied_response = self.client.get(reverse("dashboard:home"), {"state": "applied"})
        interview_response = self.client.get(reverse("dashboard:home"), {"state": "interview"})
        follow_up = VacancyFollowUp.objects.get(profile=self.profile, vacancy=self.vacancy)
        follow_up.status = VacancyFollowUp.Status.FINALIZED
        follow_up.save(update_fields=["status"])
        finalized_response = self.client.get(reverse("dashboard:home"), {"state": "finalized"})

        self.assertNotContains(default_response, "Analista de procesos")
        self.assertContains(applied_response, "Analista de procesos")
        self.assertContains(interview_response, "No hay vacantes en entrevista")
        self.assertContains(finalized_response, "Analista de procesos")

    def test_discarded_vacancy_can_be_restored_to_previous_state(self):
        VacancyFollowUp.objects.create(
            profile=self.profile,
            vacancy=self.vacancy,
            status=VacancyFollowUp.Status.DISCARDED,
            previous_status=VacancyFollowUp.Status.APPLIED,
        )
        self.client.force_login(self.user)

        discarded_response = self.client.get(reverse("dashboard:home"), {"state": "discarded"})
        self.assertContains(discarded_response, "Restaurar vacante")
        self.assertContains(discarded_response, "Analista de procesos")

        response = self.client.post(
            reverse("dashboard:update_follow_up", args=[self.vacancy.pk]), {"status": "restore"}
        )

        self.assertRedirects(response, "/?state=applied", fetch_redirect_response=False)
        applied_response = self.client.get(reverse("dashboard:home"), {"state": "applied"})
        discarded_response = self.client.get(reverse("dashboard:home"), {"state": "discarded"})
        self.assertContains(applied_response, "Analista de procesos")
        self.assertContains(discarded_response, "No hay vacantes descartadas")

    def test_discarded_vacancy_stays_out_of_recommendations_after_new_profile_revision_analysis(self):
        follow_up = VacancyFollowUp.objects.create(
            profile=self.profile,
            vacancy=self.vacancy,
            status=VacancyFollowUp.Status.DISCARDED,
            previous_status=VacancyFollowUp.Status.PENDING,
        )
        self.profile.revision_number = 2
        self.profile.save(update_fields=["revision_number"])
        new_revision = self.profile.revisions.create(version=2)
        new_config = MatchingConfig.objects.create(
            version=2,
            rubric_version=RUBRIC_VERSION,
            analysis_prompt="Prompt actualizado",
            organization_prompt="Organiza",
            is_active=False,
        )
        VacancyAnalysis.objects.create(
            profile=self.profile,
            profile_revision=new_revision,
            vacancy=self.vacancy,
            matching_config=new_config,
            status=VacancyAnalysis.Status.COMPLETED,
            score=9,
            score_breakdown={"skills": {"score": 4}},
        )
        self.client.force_login(self.user)

        recommendations = self.client.get(reverse("dashboard:home"))
        discarded = self.client.get(reverse("dashboard:home"), {"state": "discarded"})
        follow_up.refresh_from_db()

        self.assertEqual(follow_up.status, VacancyFollowUp.Status.DISCARDED)
        self.assertEqual(recommendations.context["follow_up_counts"]["pending"], 0)
        self.assertNotContains(recommendations, "Analista de procesos")
        self.assertEqual(discarded.context["follow_up_counts"]["discarded"], 1)
        self.assertContains(discarded, "Analista de procesos")

    def test_archived_discarded_vacancy_does_not_reappear_after_new_analysis(self):
        VacancyFollowUp.objects.create(
            profile=self.profile,
            vacancy=self.vacancy,
            status=VacancyFollowUp.Status.DISCARDED,
            previous_status=VacancyFollowUp.Status.PENDING,
            archived_at=timezone.now(),
        )
        updated_config = MatchingConfig.objects.create(
            version=2,
            rubric_version=RUBRIC_VERSION,
            analysis_prompt="Prompt actualizado",
            organization_prompt="Organiza",
            is_active=False,
        )
        VacancyAnalysis.objects.create(
            profile=self.profile,
            profile_revision=self.revision,
            vacancy=self.vacancy,
            matching_config=updated_config,
            status=VacancyAnalysis.Status.COMPLETED,
            score=9,
            score_breakdown={"skills": {"score": 4}},
        )
        self.client.force_login(self.user)

        recommendations = self.client.get(reverse("dashboard:home"))
        discarded = self.client.get(reverse("dashboard:home"), {"state": "discarded"})

        self.assertEqual(recommendations.context["follow_up_counts"]["pending"], 0)
        self.assertEqual(discarded.context["follow_up_counts"]["discarded"], 0)
        self.assertNotContains(recommendations, "Analista de procesos")
        self.assertNotContains(discarded, "Analista de procesos")

    def test_discarded_state_for_one_profile_does_not_hide_vacancy_from_another(self):
        VacancyFollowUp.objects.create(
            profile=self.profile,
            vacancy=self.vacancy,
            status=VacancyFollowUp.Status.DISCARDED,
            previous_status=VacancyFollowUp.Status.PENDING,
        )
        self.other_profile.revision_number = 1
        self.other_profile.save(update_fields=["revision_number"])
        VacancyAnalysis.objects.create(
            profile=self.other_profile,
            profile_revision=self.other_revision,
            vacancy=self.vacancy,
            matching_config=self.config,
            status=VacancyAnalysis.Status.COMPLETED,
            score=8,
            score_breakdown={"skills": {"score": 4}},
        )
        self.client.force_login(self.other_user)

        response = self.client.get(reverse("dashboard:home"))

        self.assertContains(response, "Analista de procesos")
        self.assertEqual(response.context["follow_up_counts"]["pending"], 1)

    def test_dashboard_tabs_are_ordered_and_show_unique_counts_after_state_change(self):
        VacancyAnalysis.objects.create(
            profile=self.profile,
            profile_revision=self.revision,
            vacancy=self.vacancy,
            matching_config=self.config,
            status=VacancyAnalysis.Status.COMPLETED,
            score=7,
            score_breakdown={"skills": {"score": 3}},
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("dashboard:update_follow_up", args=[self.vacancy.pk]), {"status": "applied"}
        )
        self.assertRedirects(response, "/?state=applied", fetch_redirect_response=False)

        response = self.client.get(reverse("dashboard:home"), {"state": "applied"})
        self.assertEqual(
            response.context["follow_up_counts"],
            {"pending": 0, "discarded": 0, "applied": 1, "in_progress": 0, "interview": 0, "finalized": 0},
        )
        self.assertEqual(len(response.context["analyses"]), 1)
        nav = response.content.decode().split('<nav class="dashboard-tabs"', 1)[1].split("</nav>", 1)[0]
        ordered_tabs = ["Por analizar", "Recomendaciones", "Aplicadas", "En proceso", "Entrevista", "Finalizadas", "Descartadas"]
        positions = [nav.index(tab) for tab in ordered_tabs]
        self.assertEqual(positions, sorted(positions))
        self.assertContains(response, "<span>1</span>")
        self.assertContains(response, "<span>0</span>")

        discarded = self.client.post(
            reverse("dashboard:update_follow_up", args=[self.vacancy.pk]), {"status": "discarded"}
        )
        self.assertRedirects(discarded, "/?state=discarded", fetch_redirect_response=False)
        response = self.client.get(reverse("dashboard:home"), {"state": "discarded"})
        self.assertEqual(response.context["follow_up_counts"]["applied"], 0)
        self.assertEqual(response.context["follow_up_counts"]["discarded"], 1)
        self.assertContains(response, "Restaurar vacante")

        restored = self.client.post(
            reverse("dashboard:update_follow_up", args=[self.vacancy.pk]), {"status": "restore"}
        )
        self.assertRedirects(restored, "/?state=applied", fetch_redirect_response=False)

    def test_recommendations_are_sorted_by_full_decimal_score(self):
        self.profile.min_score = 8
        self.profile.save(update_fields=["min_score"])
        vacancies = []
        for index, score in enumerate((Decimal("8.2"), Decimal("8.9"), Decimal("8.5"))):
            vacancy = Vacancy.objects.create(
                source="elempleo_co",
                title=f"Recomendación decimal {index}",
                original_url=f"https://jobs.example.test/decimal-order-{index}",
            )
            vacancies.append(vacancy)
            VacancyAnalysis.objects.create(
                profile=self.profile,
                profile_revision=self.revision,
                vacancy=vacancy,
                matching_config=self.config,
                status=VacancyAnalysis.Status.COMPLETED,
                score=score,
                score_breakdown={"skills": {"score": 4}},
            )
        VacancyFollowUp.objects.create(
            profile=self.profile,
            vacancy=self.vacancy,
            status=VacancyFollowUp.Status.APPLIED,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(
            [analysis.vacancy.title for analysis in response.context["analyses"]],
            ["Recomendación decimal 1", "Recomendación decimal 2", "Recomendación decimal 0"],
        )

    def test_follow_up_stages_sort_by_state_date_and_ignore_profile_minimum(self):
        self.profile.min_score = 9
        self.profile.save(update_fields=["min_score"])
        old_vacancy = Vacancy.objects.create(
            source="elempleo_co", title="Aplicada antes", original_url="https://jobs.example.test/applied-old"
        )
        new_vacancy = Vacancy.objects.create(
            source="elempleo_co", title="Aplicada reciente", original_url="https://jobs.example.test/applied-new"
        )
        for vacancy, score, age in (
            (old_vacancy, Decimal("9.8"), 10),
            (new_vacancy, Decimal("4.2"), 1),
        ):
            VacancyAnalysis.objects.create(
                profile=self.profile,
                profile_revision=self.revision,
                vacancy=vacancy,
                matching_config=self.config,
                status=VacancyAnalysis.Status.COMPLETED,
                score=score,
                score_breakdown={"skills": {"score": 4}},
            )
            VacancyFollowUp.objects.create(
                profile=self.profile,
                vacancy=vacancy,
                status=VacancyFollowUp.Status.APPLIED,
                state_changed_at=timezone.now() - timedelta(days=age),
            )
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard:home"), {"state": "applied", "score_min": "10"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["score_filter"], None)
        self.assertEqual(
            [analysis.vacancy.title for analysis in response.context["analyses"]],
            ["Aplicada reciente", "Aplicada antes"],
        )
        self.assertContains(response, "Aplicada reciente")
        self.assertContains(response, "Aplicada antes")
        self.assertNotContains(response, 'type="range" name="score_min"')

    def test_pending_tab_count_is_zero_when_no_analysis_is_waiting(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard:home"))

        self.assertContains(response, "Por analizar<span>0</span>")

    def test_pagination_keeps_selected_follow_up_state(self):
        VacancyFollowUp.objects.create(
            profile=self.profile, vacancy=self.vacancy, status=VacancyFollowUp.Status.APPLIED
        )
        for index in range(20):
            vacancy = Vacancy.objects.create(
                source="elempleo_co",
                title=f"Vacante aplicada {index}",
                original_url=f"https://jobs.example.test/applied-page-{index}",
            )
            VacancyAnalysis.objects.create(
                profile=self.profile,
                profile_revision=self.revision,
                vacancy=vacancy,
                matching_config=self.config,
                status=VacancyAnalysis.Status.COMPLETED,
                score=8,
                score_breakdown={"skills": {"score": 4}},
            )
            VacancyFollowUp.objects.create(
                profile=self.profile, vacancy=vacancy, status=VacancyFollowUp.Status.APPLIED
            )
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard:home"), {"state": "applied"})

        self.assertContains(response, "?state=applied&amp;page=2")
        next_page = self.client.get(reverse("dashboard:home"), {"state": "applied", "page": "2"})
        self.assertEqual(next_page.status_code, 200)
        self.assertEqual(next_page.context["follow_up_status"], VacancyFollowUp.Status.APPLIED)

    def test_update_rejects_unknown_state(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("dashboard:update_follow_up", args=[self.vacancy.pk]), {"status": "hired"}
        )

        self.assertEqual(response.status_code, 400)

    def test_changing_follow_up_state_restarts_its_age(self):
        self.client.force_login(self.user)
        follow_up = VacancyFollowUp.objects.create(
            profile=self.profile,
            vacancy=self.vacancy,
            status=VacancyFollowUp.Status.APPLIED,
        )
        old_state_date = timezone.now() - timedelta(days=5)
        VacancyFollowUp.objects.filter(pk=follow_up.pk).update(state_changed_at=old_state_date)

        response = self.client.post(
            reverse("dashboard:update_follow_up", args=[self.vacancy.pk]),
            {"status": VacancyFollowUp.Status.IN_PROGRESS},
        )

        follow_up.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(follow_up.status, VacancyFollowUp.Status.IN_PROGRESS)
        self.assertGreater(follow_up.state_changed_at, old_state_date)

    def test_update_cannot_change_vacancy_for_another_profile(self):
        other_vacancy = Vacancy.objects.create(
            source="elempleo_co",
            title="Vacante de otra persona",
            original_url="https://jobs.example.test/other-profile",
        )
        VacancyAnalysis.objects.create(
            profile=self.other_profile,
            profile_revision=self.other_revision,
            vacancy=other_vacancy,
            matching_config=self.config,
            status=VacancyAnalysis.Status.COMPLETED,
            score=8,
            score_breakdown={"skills": {"score": 4}},
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("dashboard:update_follow_up", args=[other_vacancy.pk]), {"status": "applied"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(VacancyFollowUp.objects.exists())

    def test_update_changes_only_follow_up_and_survives_new_analysis(self):
        self.client.force_login(self.user)

        endpoint = reverse("dashboard:update_follow_up", args=[self.vacancy.pk])
        self.client.post(endpoint, {"status": "applied"})
        self.client.post(endpoint, {"status": "in_progress"})
        response = self.client.post(endpoint, {"status": "interview"})

        self.assertRedirects(response, "/?state=interview", fetch_redirect_response=False)
        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, VacancyAnalysis.Status.COMPLETED)
        self.assertEqual(self.analysis.score, 8)
        follow_up = VacancyFollowUp.objects.get(profile=self.profile, vacancy=self.vacancy)
        self.assertEqual(follow_up.status, VacancyFollowUp.Status.INTERVIEW)

        reprocessed_config = MatchingConfig.objects.create(
            version=2,
            rubric_version=RUBRIC_VERSION,
            analysis_prompt="Prompt nuevo",
            organization_prompt="Organiza",
            is_active=False,
        )
        VacancyAnalysis.objects.create(
            profile=self.profile,
            profile_revision=self.revision,
            vacancy=self.vacancy,
            matching_config=reprocessed_config,
            status=VacancyAnalysis.Status.COMPLETED,
            score=9,
            score_breakdown={"skills": {"score": 4}},
        )

        self.assertEqual(VacancyFollowUp.objects.get(profile=self.profile, vacancy=self.vacancy).status,
                         VacancyFollowUp.Status.INTERVIEW)

    def test_update_rejects_skipped_or_backward_transitions(self):
        self.client.force_login(self.user)
        endpoint = reverse("dashboard:update_follow_up", args=[self.vacancy.pk])

        response = self.client.post(endpoint, {"status": "interview"})

        self.assertEqual(response.status_code, 400)
        self.assertFalse(VacancyFollowUp.objects.exists())

        VacancyFollowUp.objects.create(
            profile=self.profile, vacancy=self.vacancy, status=VacancyFollowUp.Status.APPLIED
        )
        response = self.client.post(endpoint, {"status": "interview"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            VacancyFollowUp.objects.get(profile=self.profile, vacancy=self.vacancy).status,
            VacancyFollowUp.Status.APPLIED,
        )

    def test_discard_from_any_stage_remembers_and_restores_that_stage(self):
        self.client.force_login(self.user)
        endpoint = reverse("dashboard:update_follow_up", args=[self.vacancy.pk])
        follow_up = VacancyFollowUp.objects.create(profile=self.profile, vacancy=self.vacancy)
        for previous_status in (
            VacancyFollowUp.Status.PENDING,
            VacancyFollowUp.Status.APPLIED,
            VacancyFollowUp.Status.IN_PROGRESS,
            VacancyFollowUp.Status.INTERVIEW,
            VacancyFollowUp.Status.FINALIZED,
        ):
            with self.subTest(previous_status=previous_status):
                follow_up.status = previous_status
                follow_up.save(update_fields=["status"])
                response = self.client.post(endpoint, {"status": "discarded"})
                self.assertRedirects(response, "/?state=discarded", fetch_redirect_response=False)
                follow_up.refresh_from_db()
                self.assertEqual(follow_up.status, VacancyFollowUp.Status.DISCARDED)
                self.assertEqual(follow_up.previous_status, previous_status)

                response = self.client.post(endpoint, {"status": "restore"})

                self.assertRedirects(response, f"/?state={previous_status}", fetch_redirect_response=False)
                follow_up.refresh_from_db()
                self.assertEqual(follow_up.status, previous_status)
