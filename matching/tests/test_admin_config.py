from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from unittest.mock import Mock, patch

from jobs.models import Vacancy
from matching.admin import MatchingConfigAdmin, VacancyAnalysisAdmin, reprocess_selected_analyses
from matching.models import DEFAULT_SEARCH_PROMPT, PROMPT_VERSION, RUBRIC_VERSION, MatchingConfig, VacancyAnalysis
from matching.services import CRITICAL_COMPLETENESS_INSTRUCTION, EVIDENCE_STATUS_INSTRUCTION, get_active_matching_config
from matching.tasks import create_analysis
from profiles.models import Profile, ProfileRevision


class VersionedConfigAdminTests(TestCase):
    def setUp(self):
        self.site = admin.site
        self.request = RequestFactory().post("/admin/matching/matchingconfig/add/")
        self.request.user = get_user_model().objects.create_superuser("owner", "owner@example.test", "long-password")
        self.request._messages = Mock()
        self.admin_view = MatchingConfigAdmin(MatchingConfig, self.site)

    def test_saving_new_config_versions_it_and_keeps_history(self):
        first = MatchingConfig.objects.create(
            version=1,
            search_prompt="Primer prompt de búsqueda",
            analysis_prompt="Primer análisis",
            organization_prompt="Primera descripción",
        )
        second = MatchingConfig(
            search_prompt="Prompt ajustado",
            analysis_prompt="Análisis ajustado",
            organization_prompt="Descripción ajustada",
            parameters={"temperature": 0.2, "weights": {"skills": 0.5}},
        )

        self.admin_view.save_model(self.request, second, form=None, change=True)

        first.refresh_from_db()
        active = MatchingConfig.objects.get(is_active=True)
        self.assertFalse(first.is_active)
        self.assertEqual(first.analysis_prompt, "Primer análisis")
        self.assertEqual(active.version, 2)
        self.assertEqual(active.search_prompt, "Prompt ajustado")
        self.assertEqual(active.analysis_prompt, "Análisis ajustado")
        self.assertEqual(active.rubric_version, RUBRIC_VERSION)
        self.assertEqual(active.parameters["rubric"]["critical_requirement_deduction"], "2.0")

    def test_prompt_upgrade_preserves_parameters_and_historical_analysis(self):
        old = MatchingConfig.objects.create(
            version=1, rubric_version=RUBRIC_VERSION, prompt_version=PROMPT_VERSION - 1,
            analysis_prompt="Prompt anterior", organization_prompt="Organización anterior",
            parameters={"temperature": 0.2, "rubric": {"critical_requirement_deduction": "1.5"}},
        )
        profile = Profile.objects.create(owner=self.request.user, cv_file="cv.pdf", revision_number=1)
        revision = ProfileRevision.objects.create(profile=profile, version=1, cv_file_path="cv.pdf")
        vacancy = Vacancy.objects.create(source="ejemplo", title="Analista", original_url="https://example.test/analista")
        historical = VacancyAnalysis.objects.create(
            profile=profile, profile_revision=revision, vacancy=vacancy, matching_config=old,
            status=VacancyAnalysis.Status.COMPLETED, score=7,
        )

        current = get_active_matching_config()

        old.refresh_from_db()
        historical.refresh_from_db()
        self.assertFalse(old.is_active)
        self.assertEqual(old.analysis_prompt, "Prompt anterior")
        self.assertEqual(historical.matching_config_id, old.pk)
        self.assertEqual(historical.score, 7)
        self.assertEqual(current.prompt_version, PROMPT_VERSION)
        self.assertIn(CRITICAL_COMPLETENESS_INSTRUCTION, current.analysis_prompt)
        self.assertIn("requirement de máximo 180 caracteres", current.analysis_prompt)
        self.assertIn("evidence de máximo 240 caracteres", current.analysis_prompt)
        self.assertIn("cumple, sin_evidencia o contradicho", current.analysis_prompt)
        self.assertIn(EVIDENCE_STATUS_INSTRUCTION, current.analysis_prompt)
        self.assertEqual(current.parameters["rubric"]["critical_requirement_deduction"], "1.5")

    def test_admin_config_versions_custom_critical_deduction(self):
        config = MatchingConfig(
            search_prompt="Busca", analysis_prompt="Evalúa", organization_prompt="Ordena",
            parameters={"temperature": 0.1, "rubric": {"critical_requirement_deduction": "1.5"}},
        )

        self.admin_view.save_model(self.request, config, form=None, change=False)

        self.assertEqual(config.parameters["rubric"]["critical_requirement_deduction"], "1.5")

    def test_new_config_form_starts_from_active_prompts(self):
        active = MatchingConfig.objects.create(
            version=1,
            search_prompt="Búsqueda vigente",
            analysis_prompt="Análisis vigente",
            organization_prompt="Descripción vigente",
            parameters={"temperature": 0.2},
        )

        initial = self.admin_view.get_changeform_initial_data(self.request)

        self.assertEqual(initial["search_prompt"], active.search_prompt)
        self.assertEqual(initial["analysis_prompt"], active.analysis_prompt)
        self.assertEqual(initial["organization_prompt"], active.organization_prompt)
        self.assertEqual(initial["parameters"], active.parameters)

    def test_first_config_gets_default_search_prompt(self):
        config = get_active_matching_config()

        self.assertEqual(config.search_prompt, DEFAULT_SEARCH_PROMPT)

    @patch("matching.tasks.analyze_vacancy_for_profile.delay")
    def test_reprocessing_creates_new_result_with_current_profile_and_config(self, queue):
        user = get_user_model().objects.create_user("member")
        profile = Profile.objects.create(owner=user, cv_file="profiles/1/cv/v1.pdf", revision_number=1)
        revision = ProfileRevision.objects.create(profile=profile, version=1, cv_file_path=profile.cv_file.name)
        vacancy = Vacancy.objects.create(
            source="elempleo_co",
            title="Vacante",
            original_url="https://www.elempleo.com/co/ofertas-trabajo/vacante-22",
        )
        old_config = MatchingConfig.objects.create(
            version=1, analysis_prompt="old", organization_prompt="old", is_active=False
        )
        new_config = MatchingConfig.objects.create(
            version=2,
            rubric_version=RUBRIC_VERSION,
            prompt_version=PROMPT_VERSION,
            analysis_prompt="new",
            organization_prompt="new",
        )
        previous = VacancyAnalysis.objects.create(
            profile=profile,
            profile_revision=revision,
            vacancy=vacancy,
            matching_config=old_config,
            status=VacancyAnalysis.Status.COMPLETED,
            score=55,
        )
        analysis_admin = VacancyAnalysisAdmin(VacancyAnalysis, self.site)
        queryset = VacancyAnalysis.objects.filter(pk=previous.pk)

        reprocess_selected_analyses(analysis_admin, self.request, queryset)

        new = VacancyAnalysis.objects.exclude(pk=previous.pk).get()
        self.assertEqual(new.matching_config, new_config)
        self.assertEqual(new.status, VacancyAnalysis.Status.PENDING)
        self.assertEqual(new.profile_revision, revision)
