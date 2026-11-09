from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from jobs.models import Vacancy
from matching.models import RUBRIC_VERSION, MatchingConfig, VacancyAnalysis, VacancyOrganization
from profiles.models import Profile, ProfileRevision
from profiles.tests.helpers import mark_tour_completed


class VacancyLinkTests(TestCase):
    def test_dashboard_links_to_original_and_only_shows_organized_description(self):
        user = get_user_model().objects.create_user("member", password="pass")
        mark_tour_completed(user)
        profile = Profile.objects.create(owner=user, cv_file="profiles/1/cv/v1.pdf", revision_number=1)
        revision = ProfileRevision.objects.create(profile=profile, version=1)
        config = MatchingConfig.objects.create(
            version=1, rubric_version=RUBRIC_VERSION, analysis_prompt="P", organization_prompt="O"
        )
        vacancy = Vacancy.objects.create(
            source="elempleo_co",
            title="Coordinadora de proyectos",
            description="TEXTO ORIGINAL QUE NO DEBE MOSTRARSE",
            original_url="https://www.elempleo.com/co/ofertas-trabajo/coordinadora-77",
        )
        organization = VacancyOrganization.objects.create(
            vacancy=vacancy, matching_config=config, content_hash="version-1",
            status=VacancyOrganization.Status.COMPLETED,
            content={"summary": "Lidera proyectos y coordina equipos.",
                     "keywords": ["Lidera proyectos", "coordina equipos"]},
        )
        VacancyAnalysis.objects.create(
            profile=profile,
            profile_revision=revision,
            vacancy=vacancy,
            matching_config=config,
            organization=organization,
            organization_status=VacancyAnalysis.OrganizationStatus.COMPLETED,
            status=VacancyAnalysis.Status.COMPLETED,
            organized_description="Lidera proyectos y coordina equipos.",
            organized_content={"keywords": ["Lidera proyectos", "coordina equipos"]},
            score=9,
            score_breakdown={"requisitos": {"score": 4}},
            reasons=["Experiencia liderando"],
            gaps=["No menciona PMP"],
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard:home"))

        self.assertContains(response, "https://www.elempleo.com/co/ofertas-trabajo/coordinadora-77")
        self.assertContains(response, "Lidera proyectos")
        self.assertContains(response, "coordina equipos")
        self.assertNotContains(response, "Lidera proyectos y coordina equipos.")
        self.assertNotContains(response, "TEXTO ORIGINAL QUE NO DEBE MOSTRARSE")
        self.assertNotContains(response, "Postularme")
