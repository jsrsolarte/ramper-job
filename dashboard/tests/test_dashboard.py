from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from jobs.models import Vacancy
from dashboard.models import VacancyFollowUp
from dashboard.score_display import score_star_label, score_star_percent
from matching.models import RUBRIC_VERSION, MatchingConfig, VacancyAnalysis, VacancyOrganization
from profiles.models import Profile, ProfileRevision
from profiles.tests.helpers import mark_tour_completed


class DashboardPrivacyTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.first = user_model.objects.create_user("first", password="pass")
        self.second = user_model.objects.create_user("second", password="pass")
        mark_tour_completed(self.first, self.second)
        self.first_profile = Profile.objects.create(owner=self.first, cv_file="profiles/1/cv/v1.pdf", revision_number=1)
        self.second_profile = Profile.objects.create(owner=self.second, cv_file="profiles/2/cv/v1.pdf", revision_number=1)
        self.first_revision = ProfileRevision.objects.create(profile=self.first_profile, version=1)
        self.second_revision = ProfileRevision.objects.create(profile=self.second_profile, version=1)
        self.config = MatchingConfig.objects.create(
            version=1, rubric_version=RUBRIC_VERSION, analysis_prompt="Prompt", organization_prompt="Organiza"
        )
        self.best = self._vacancy("Mejor vacante", "https://jobs.example.test/best", 9, self.first_profile, self.first_revision)
        self.lower = self._vacancy("Otra vacante", "https://jobs.example.test/other", 7, self.first_profile, self.first_revision)
        self.hidden = self._vacancy("Vacante ajena", "https://jobs.example.test/private", 99, self.second_profile, self.second_revision)

    def _vacancy(self, title, url, score, profile, revision):
        vacancy = Vacancy.objects.create(source="elempleo_co", title=title, original_url=url)
        return VacancyAnalysis.objects.create(
            profile=profile,
            profile_revision=revision,
            vacancy=vacancy,
            matching_config=self.config,
            status=VacancyAnalysis.Status.COMPLETED,
            organized_description=f"Descripción organizada de {title}",
            score=score,
            score_breakdown={"requisitos": {"score": float(score)}},
            reasons=["Experiencia coincide"],
            gaps=["Revisar disponibilidad"],
        )

    def test_tab_counts_follow_current_states_independently_of_profile_threshold_and_list_filter(self):
        self.first_profile.min_score = 8
        self.first_profile.save(update_fields=['min_score'])
        applied = self._vacancy('Aplicada bajo el mínimo', 'https://jobs.example.test/applied', 6, self.first_profile, self.first_revision)
        VacancyFollowUp.objects.create(profile=self.first_profile, vacancy=applied.vacancy, status=VacancyFollowUp.Status.APPLIED)
        self.client.force_login(self.first)

        for params in ({'state': 'pending'}, {'state': 'applied'}, {'state': 'pending', 'score_min': '10'}):
            response = self.client.get(reverse('dashboard:home'), params)
            self.assertEqual(response.context['follow_up_counts']['pending'], 2)
            self.assertEqual(response.context['follow_up_counts']['applied'], 1)
        self.assertContains(self.client.get(reverse('dashboard:home'), {'state': 'applied'}), 'Aplicada bajo el mínimo')

    def test_dashboard_only_shows_owner_results_sorted_by_score(self):
        self.best.vacancy.raw_data = {
            "publication_label": "Ayer",
            "details": {
                "city": "Bogotá", "address": "Av. 68 # 13-50", "modality": "presencial",
                "list_salary": "$4 a $4,5 millones", "education": "Universitaria",
                "salary_periodicity": "mensuales", "area": "Calidad",
                "experience": "1 año", "schedule": "Lunes a viernes", "vacancy_count": "20",
            },
        }
        self.best.vacancy.save(update_fields=["raw_data"])
        self.best.vacancy.salary = "$4.214.000 pagos mensuales"
        self.best.vacancy.contract_type = "Obra o labor"
        self.best.vacancy.save(update_fields=["salary", "contract_type"])
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mejor vacante")
        self.assertContains(response, "Publicada Ayer")
        self.assertContains(response, "<dt>Ubicación</dt>")
        self.assertContains(response, "<dd>Bogotá · Av. 68 # 13-50</dd>")
        self.assertContains(response, "Av. 68 # 13-50")
        self.assertContains(response, "<dt>Modalidad</dt>")
        self.assertContains(response, "<dt>Periodicidad</dt>")
        self.assertContains(response, "<dt>Tipo de contrato</dt>")
        self.assertContains(response, "<dt>Área</dt>")
        self.assertContains(response, "<dt>Nivel educativo</dt>")
        self.assertContains(response, "<dt>Experiencia</dt>")
        self.assertContains(response, "<dt>Horario</dt>")
        self.assertContains(response, "<dt>Vacantes</dt>")
        self.assertContains(response, "$4.214.000 pagos mensuales")
        self.assertContains(response, "$4 a $4,5 millones")
        self.assertContains(response, "Ver detalles del análisis")
        self.assertContains(response, '<details class="match-details" data-tour="vacancy-details">')
        self.assertContains(response, "Otra vacante")
        self.assertNotContains(response, "Vacante ajena")
        result_ids = [analysis.pk for analysis in response.context["analyses"]]
        self.assertEqual(result_ids, [self.best.pk, self.lower.pk])

    def test_dashboard_keeps_score_visible_and_communicates_organization_status(self):
        organization = VacancyOrganization.objects.create(
            vacancy=self.best.vacancy, matching_config=self.config, content_hash="dashboard-version",
            status=VacancyOrganization.Status.PENDING,
        )
        self.best.organization = organization
        self.best.organization_status = VacancyAnalysis.OrganizationStatus.PENDING
        self.best.save(update_fields=["organization", "organization_status"])
        self.client.force_login(self.first)

        pending = self.client.get(reverse("dashboard:home"))
        self.assertContains(pending, "Compatibilidad: 9,0 de 10")
        self.assertContains(pending, "Puntaje calculado. Estamos organizando los detalles")

        organization.status = VacancyOrganization.Status.FAILED
        organization.save(update_fields=["status"])
        self.best.organization_status = VacancyAnalysis.OrganizationStatus.FAILED
        self.best.save(update_fields=["organization_status"])
        failed = self.client.get(reverse("dashboard:home"))
        self.assertContains(failed, "no se pudieron organizar los detalles")
        self.assertContains(failed, "Mejor vacante")

    def test_scores_use_half_star_visual_rounding_but_keep_exact_accessible_values(self):
        self.best.score = 8.5
        self.best.save(update_fields=["score"])
        self.lower.score = 8.4
        self.lower.save(update_fields=["score"])
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual([item.score_star_percent for item in response.context["analyses"]], [90, 80])
        self.assertEqual([item.score_star_label for item in response.context["analyses"]], ["4,5", "4,0"])
        self.assertContains(response, 'aria-label="Compatibilidad: 8,5 de 10. Equivalente visual: 4,5 de 5 estrellas"')
        self.assertContains(response, 'style="--score-fill: 90%;"')
        self.assertContains(response, 'style="--score-fill: 80%;"')
        self.assertNotContains(response, 'class="score-exact"')
        self.assertEqual(score_star_percent(8.49), 80)
        self.assertEqual(score_star_percent(8.5), 90)
        self.assertEqual(score_star_percent(9.5), 100)
        self.assertEqual(score_star_label(0), "0,0")

    def test_dashboard_shows_relative_publication_analysis_and_current_state_times(self):
        now = timezone.now()
        self.best.completed_at = now - timedelta(hours=2)
        self.best.save(update_fields=["completed_at"])
        self.best.vacancy.published_at = now - timedelta(days=1)
        self.best.vacancy.save(update_fields=["published_at"])
        self.client.force_login(self.first)

        recommendation = self.client.get(reverse("dashboard:home"))

        self.assertContains(recommendation, "Analizada hace 2 horas")
        self.assertContains(recommendation, 'aria-label="Analizada ')
        self.assertContains(recommendation, "Publicada hace 1 día")
        self.assertContains(recommendation, 'aria-label="Publicada ')

        from dashboard.models import VacancyFollowUp

        follow_up = VacancyFollowUp.objects.create(
            profile=self.first_profile,
            vacancy=self.best.vacancy,
            status=VacancyFollowUp.Status.APPLIED,
            state_changed_at=now - timedelta(days=3),
        )
        applied = self.client.get(reverse("dashboard:home"), {"state": "applied"})

        self.assertContains(applied, "Aplicada hace 3 días")
        self.assertContains(applied, 'aria-label="Aplicada ')
        self.assertNotContains(applied, "Analizada hace")
        self.assertEqual(follow_up.state_changed_at, now - timedelta(days=3))

    def test_dashboard_score_filter_is_independent_of_profile_discard_threshold(self):
        self.first_profile.min_score = 8
        self.first_profile.save(update_fields=["min_score"])
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:home"), {"score_min": "5"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item.pk for item in response.context["analyses"]], [self.best.pk, self.lower.pk])
        self.assertEqual(self.first_profile.min_score, 8)

    def test_invalid_dashboard_score_filter_is_omitted_independently_of_profile_threshold(self):
        self.first_profile.min_score = 8
        self.first_profile.save(update_fields=["min_score"])
        self.client.force_login(self.first)

        for score_filter in ("-1", "11", "invalid", "1.5"):
            with self.subTest(score_filter=score_filter):
                response = self.client.get(reverse("dashboard:home"), {"score_min": score_filter})
                self.assertEqual(response.status_code, 200)
                self.assertEqual([item.pk for item in response.context["analyses"]], [self.best.pk, self.lower.pk])
                self.assertIsNone(response.context["score_filter"])

    def test_missing_dashboard_score_filter_shows_all_recommendations(self):
        self.first_profile.min_score = 8
        self.first_profile.save(update_fields=["min_score"])
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual([item.pk for item in response.context["analyses"]], [self.best.pk, self.lower.pk])
        self.assertIsNone(response.context["score_filter"])

    def test_dashboard_score_star_options_are_independent_of_profile_threshold(self):
        self.first_profile.min_score = 8
        self.first_profile.save(update_fields=["min_score"])
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:home"))

        self.assertContains(response, 'aria-label="Puntaje mínimo de compatibilidad"')
        self.assertContains(response, 'aria-label="Mostrar todas las recomendaciones"')
        self.assertContains(response, 'aria-label="Mostrar recomendaciones con 4 estrellas o más"')
        self.assertContains(response, 'href="?score_min=0"')
        self.assertNotContains(response, 'type="range" name="score_min"')
        self.assertNotContains(response, 'Mínimo de tu perfil: 4 estrellas')
        self.assertEqual(response.context["score_filter_value"], 0)

        response = self.client.get(reverse("dashboard:home"), {"score_min": "10"})
        self.assertContains(response, 'href="?score_min=10" aria-current="true" aria-label="Mostrar recomendaciones con 5 estrellas o más"')
        self.assertEqual(response.context["score_filter_value"], 10)

    def test_dashboard_score_filter_is_preserved_when_paginating(self):
        for index in range(20):
            self._vacancy(
                f"Vacante adicional {index}",
                f"https://jobs.example.test/additional-{index}",
                8,
                self.first_profile,
                self.first_revision,
            )
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:home"), {"score_min": "8"})

        self.assertContains(response, "?score_min=8&amp;page=2")
        self.assertEqual(response.context["analyses"].paginator.count, 21)
        self.assertEqual(self.first_profile.min_score, 0)

        second_page = self.client.get(reverse("dashboard:home"), {"score_min": "8", "page": "2"})

        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(second_page.context["score_filter"], 8)
        self.assertEqual(second_page.context["analyses"].paginator.count, 21)

    def test_elided_pagination_at_start_middle_and_end_preserves_filters(self):
        vacancies = [Vacancy(source="elempleo_co", title=f"Vacante {i}",
                    original_url=f"https://jobs.example.test/long-{i}", dedupe_key=f"long-{i}") for i in range(220)]
        Vacancy.objects.bulk_create(vacancies)
        VacancyAnalysis.objects.bulk_create([
            VacancyAnalysis(profile=self.first_profile, profile_revision=self.first_revision,
                vacancy=vacancy, matching_config=self.config, status=VacancyAnalysis.Status.COMPLETED,
                score=9, score_breakdown={"skills": {"score": 3}})
            for vacancy in vacancies
        ])
        self.client.force_login(self.first)
        for page_number in (1, 6, 12):
            response = self.client.get(reverse("dashboard:home"), {"state": "pending", "score_min": "8", "page": page_number})
            navigation = response.context["page_navigation"]
            numbers = [item["number"] for item in navigation if "number" in item]
            self.assertIn(1, numbers)
            self.assertIn(12, numbers)
            self.assertIn(page_number, numbers)
            self.assertTrue(any(item.get("ellipsis") for item in navigation))
            for item in navigation:
                if "querystring" in item:
                    self.assertIn("state=pending", item["querystring"])
                    self.assertIn("score_min=8", item["querystring"])
            self.assertEqual(next(item for item in navigation if item.get("current"))["number"], page_number)
    def test_empty_dashboard_score_filter_has_a_clear_action(self):
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:home"), {"score_min": "10"})

        self.assertContains(response, "No hay recomendaciones con 5 estrellas o más")
        self.assertContains(response, "Quitar filtro del listado")
        self.assertEqual(self.first_profile.min_score, 0)

    def test_dashboard_hides_completed_vacancy_outside_profile_locations(self):
        self.first_profile.locations = ["Medellín"]
        self.first_profile.save(update_fields=["locations"])
        self.first_revision.locations = ["Medellín"]
        self.first_revision.save(update_fields=["locations"])
        vacancy = Vacancy.objects.create(
            source="elempleo_co", title="Vacante en Bogotá", location="Bogotá · Av. 68",
            raw_data={"details": {"city": "Bogotá", "modality": "presencial"}},
            original_url="https://jobs.example.test/bogota",
        )
        VacancyAnalysis.objects.create(
            profile=self.first_profile, profile_revision=self.first_revision, vacancy=vacancy,
            matching_config=self.config, status=VacancyAnalysis.Status.COMPLETED, score=99,
        )
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Vacante en Bogotá")

    def test_pending_count_excludes_a_vacancy_outside_profile_locations(self):
        self.first_profile.locations = ["Medellín"]
        self.first_profile.save(update_fields=["locations"])
        self.first_revision.locations = ["Medellín"]
        self.first_revision.save(update_fields=["locations"])
        vacancy = Vacancy.objects.create(
            source="elempleo_co", title="Pendiente en Bogotá", location="Bogotá",
            raw_data={"details": {"city": "Bogotá", "modality": "presencial"}},
            original_url="https://jobs.example.test/pending-bogota",
        )
        VacancyAnalysis.objects.create(
            profile=self.first_profile, profile_revision=self.first_revision, vacancy=vacancy,
            matching_config=self.config,
        )
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.context["pending_count"], 0)
        self.assertNotContains(response, "pendiente")

    def test_anonymous_user_must_sign_in(self):
        response = self.client.get(reverse("dashboard:home"))

        self.assertRedirects(response, f"{reverse('login')}?next=/", fetch_redirect_response=False)

    def test_pending_or_invalid_analysis_is_not_shown(self):
        pending_vacancy = Vacancy.objects.create(
            source="elempleo_co", title="Pendiente", original_url="https://jobs.example.test/pending"
        )
        VacancyAnalysis.objects.create(
            profile=self.first_profile,
            profile_revision=self.first_revision,
            vacancy=pending_vacancy,
            matching_config=self.config,
        )
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:home"))

        self.assertNotContains(response, "<h2>Pendiente</h2>")
        self.assertContains(response, "1 vacante pendiente de análisis")

    def test_pending_view_only_includes_current_revision_for_signed_in_profile(self):
        current_revision = ProfileRevision.objects.create(profile=self.first_profile, version=2)
        self.first_profile.revision_number = 2
        self.first_profile.save(update_fields=["revision_number"])
        current = Vacancy.objects.create(
            source="elempleo_co", title="Pendiente vigente", original_url="https://jobs.example.test/current-pending"
        )
        old_revision = Vacancy.objects.create(
            source="elempleo_co", title="Pendiente anterior", original_url="https://jobs.example.test/old-pending"
        )
        other_profile = Vacancy.objects.create(
            source="elempleo_co", title="Pendiente ajena", original_url="https://jobs.example.test/other-pending"
        )
        current_analysis = VacancyAnalysis.objects.create(
            profile=self.first_profile, profile_revision=current_revision, vacancy=current,
            matching_config=self.config, status=VacancyAnalysis.Status.PENDING,
        )
        VacancyAnalysis.objects.create(
            profile=self.first_profile, profile_revision=self.first_revision, vacancy=old_revision,
            matching_config=self.config, status=VacancyAnalysis.Status.PENDING,
        )
        VacancyAnalysis.objects.create(
            profile=self.second_profile, profile_revision=self.second_revision, vacancy=other_profile,
            matching_config=self.config, status=VacancyAnalysis.Status.PENDING,
        )
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:pending"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [analysis.pk for analysis in response.context["pending_analyses"]],
            [current_analysis.pk],
        )
        self.assertContains(response, "Pendiente vigente")
        self.assertNotContains(response, "Pendiente anterior")
        self.assertNotContains(response, "Pendiente ajena")

    def test_score_distribution_uses_current_results_before_filter_and_recommends_median(self):
        self.first_profile.min_score = 8
        self.first_profile.save(update_fields=["min_score"])
        self._vacancy("Puntaje cero", "https://jobs.example.test/score-zero", 0, self.first_profile, self.first_revision)
        self._vacancy("Puntaje decimal", "https://jobs.example.test/score-decimal", Decimal("1.9"), self.first_profile, self.first_revision)
        self._vacancy("Puntaje diez", "https://jobs.example.test/score-ten", 10, self.first_profile, self.first_revision)

        old_revision = ProfileRevision.objects.create(profile=self.first_profile, version=0)
        old_revision_vacancy = Vacancy.objects.create(
            source="elempleo_co", title="Resultado de revisión anterior",
            original_url="https://jobs.example.test/old-revision-score",
        )
        VacancyAnalysis.objects.create(
            profile=self.first_profile, profile_revision=old_revision, vacancy=old_revision_vacancy,
            matching_config=self.config, status=VacancyAnalysis.Status.COMPLETED, score=8,
            score_breakdown={"requisitos": {"score": 4}},
        )
        old_rubric = MatchingConfig.objects.create(
            version=2, rubric_version=RUBRIC_VERSION - 1, analysis_prompt="Antiguo",
            organization_prompt="Organiza", is_active=False,
        )
        old_rubric_vacancy = Vacancy.objects.create(
            source="elempleo_co", title="Resultado de rúbrica anterior",
            original_url="https://jobs.example.test/old-rubric-score",
        )
        VacancyAnalysis.objects.create(
            profile=self.first_profile, profile_revision=self.first_revision, vacancy=old_rubric_vacancy,
            matching_config=old_rubric, status=VacancyAnalysis.Status.COMPLETED, score=8,
            score_breakdown={"requisitos": {"score": 4}},
        )
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:home"))
        analysis_page = self.client.get(reverse("dashboard:analysis"))

        self.assertEqual(response.context["score_distribution_sample_size"], 5)
        self.assertEqual([band["count"] for band in response.context["score_distribution"]], [1, 1, 0, 0, 0, 0, 0, 1, 0, 2])
        self.assertEqual(response.context["score_recommended_min"], 7)
        self.assertEqual(response.context["score_recommended_count"], 3)
        self.assertTrue(response.context["score_recommendation_below_profile"])
        self.assertContains(analysis_page, "Distribución de puntajes")
        self.assertContains(analysis_page, "Puedes usarlo como filtro temporal del listado")
        self.assertContains(analysis_page, 'href="/?score_min=7"')
        self.assertNotContains(response, "Distribución de puntajes")
        self.assertContains(response, 'href="/analisis/"')
        self.assertEqual(self.first_profile.min_score, 8)

    def test_applying_score_suggestion_only_changes_temporary_filter(self):
        self._vacancy("Puntaje cero", "https://jobs.example.test/suggest-zero", 0, self.first_profile, self.first_revision)
        self._vacancy("Puntaje siete", "https://jobs.example.test/suggest-seven", 7, self.first_profile, self.first_revision)
        self._vacancy("Puntaje diez", "https://jobs.example.test/suggest-ten", 10, self.first_profile, self.first_revision)
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:home"))
        analysis_page = self.client.get(reverse("dashboard:analysis"))

        self.assertEqual(response.context["score_recommended_min"], 7)
        self.assertContains(analysis_page, 'href="/?score_min=7"')
        filtered = self.client.get(reverse("dashboard:home"), {"score_min": "7"})
        self.assertEqual(filtered.context["score_filter"], 7)
        self.assertEqual(self.first_profile.min_score, 0)
        selected = next(option for option in filtered.context["score_filter_options"] if option["value"] == 7)
        self.assertTrue(selected["selected"])

    def test_score_distribution_explains_insufficient_sample_and_empty_state(self):
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:analysis"))

        self.assertEqual(response.context["score_distribution_sample_size"], 2)
        self.assertIsNone(response.context["score_recommended_min"])
        self.assertContains(response, "Necesitas al menos cinco análisis vigentes")
        self.assertNotContains(response, "Aplicar sugerencia al filtro")

        VacancyAnalysis.objects.filter(profile=self.first_profile).delete()
        empty = self.client.get(reverse("dashboard:analysis"))
        self.assertEqual(empty.context["score_distribution_sample_size"], 0)
        self.assertContains(empty, "Aún no hay análisis vigentes para mostrar la distribución")

    def test_analysis_view_requires_sign_in_and_only_shows_owner_scores(self):
        response = self.client.get(reverse("dashboard:analysis"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('dashboard:analysis')}",
            fetch_redirect_response=False,
        )

        self.client.force_login(self.first)
        response = self.client.get(reverse("dashboard:analysis"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Vacante ajena")
        self.assertContains(response, "Análisis de puntajes")

    def test_pending_view_requires_sign_in(self):
        response = self.client.get(reverse("dashboard:pending"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('dashboard:pending')}",
            fetch_redirect_response=False,
        )

    def test_pending_view_shows_source_fields_and_publication_link_without_ai_results(self):
        vacancy = Vacancy.objects.create(
            source="elempleo_co",
            title="Analista de operaciones",
            company="Empresa Ejemplo",
            location="Medellín",
            description="Descripción original de la publicación.",
            salary="$4.000.000 mensuales",
            contract_type="Término indefinido",
            original_url="https://jobs.example.test/pending-details",
        )
        VacancyAnalysis.objects.create(
            profile=self.first_profile, profile_revision=self.first_revision, vacancy=vacancy,
            matching_config=self.config, status=VacancyAnalysis.Status.PENDING,
        )
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:pending"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Empresa Ejemplo")
        self.assertContains(response, "Analista de operaciones")
        self.assertContains(response, "Medellín")
        self.assertContains(response, "$4.000.000 mensuales")
        self.assertContains(response, "Término indefinido")
        self.assertContains(response, "Descripción original de la publicación.")
        self.assertContains(response, "https://jobs.example.test/pending-details")
        self.assertContains(response, "Fuente · elempleo_co")
        self.assertNotContains(response, "/10")
        self.assertNotContains(response, "resumen generado por IA")

    def test_pending_view_omits_source_fields_that_are_not_available(self):
        vacancy = Vacancy.objects.create(
            source="elempleo_co",
            title="Vacante incompleta",
            original_url="https://jobs.example.test/pending-incomplete",
        )
        VacancyAnalysis.objects.create(
            profile=self.first_profile, profile_revision=self.first_revision, vacancy=vacancy,
            matching_config=self.config, status=VacancyAnalysis.Status.PENDING,
        )
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:pending"))

        self.assertContains(response, "Vacante incompleta")
        self.assertContains(response, "Fuente · elempleo_co")
        self.assertContains(response, "https://jobs.example.test/pending-incomplete")
        self.assertNotContains(response, "<dt>Ubicación</dt>")
        self.assertNotContains(response, "<dt>Salario</dt>")
        self.assertNotContains(response, "<dt>Tipo de contrato</dt>")
        self.assertNotContains(response, "Descripción original")

    def test_pending_view_empty_state_does_not_show_analysis_results(self):
        self.client.force_login(self.first)

        response = self.client.get(reverse("dashboard:pending"))

        self.assertContains(response, "No hay vacantes por analizar")
        self.assertContains(response, "Cuando encontremos nuevas publicaciones")
        self.assertNotContains(response, "puntaje")
        self.assertNotContains(response, "Compatibilidad")

    def test_dashboard_navigation_connects_recommendations_and_pending_without_changing_analysis(self):
        vacancy = Vacancy.objects.create(
            source="elempleo_co", title="Pendiente de navegación",
            original_url="https://jobs.example.test/pending-navigation",
        )
        analysis = VacancyAnalysis.objects.create(
            profile=self.first_profile, profile_revision=self.first_revision, vacancy=vacancy,
            matching_config=self.config, status=VacancyAnalysis.Status.PENDING,
        )
        self.client.force_login(self.first)

        home_response = self.client.get(reverse("dashboard:home"))
        pending_response = self.client.get(reverse("dashboard:pending"))
        analysis.refresh_from_db()

        self.assertContains(home_response, f'href="{reverse("dashboard:pending")}"')
        self.assertContains(pending_response, f'href="{reverse("dashboard:home")}"')
        self.assertContains(pending_response, "Pendiente de navegación")
        self.assertEqual(analysis.status, VacancyAnalysis.Status.PENDING)
