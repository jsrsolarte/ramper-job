from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from jobs.models import Vacancy
from matching.models import MatchingConfig, VacancyAnalysis
from matching.tasks import create_analysis
from profiles.models import Profile, ProfileRevision


class HistoricalAnalysisReuseTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("history-owner")
        self.profile = Profile.objects.create(
            owner=self.user, cv_file="profiles/history/cv.pdf", revision_number=2,
        )
        self.old_revision = ProfileRevision.objects.create(
            profile=self.profile, version=1, cv_file_path="profiles/history/old.pdf",
        )
        self.current_revision = ProfileRevision.objects.create(
            profile=self.profile, version=2, cv_file_path="profiles/history/cv.pdf",
        )
        self.old_config = MatchingConfig.objects.create(
            version=1, rubric_version=2, analysis_prompt="old", organization_prompt="old", is_active=False,
        )
        self.current_config = MatchingConfig.objects.create(
            version=2, rubric_version=3, analysis_prompt="current", organization_prompt="current", is_active=False,
        )
        self.vacancy = Vacancy.objects.create(
            source="elempleo_co", title="Analista", location="Bogotá",
            original_url="https://jobs.example.test/analyst",
        )

    def test_completed_analysis_is_reused_across_profile_and_config_changes_even_when_forced(self):
        completed = VacancyAnalysis.objects.create(
            profile=self.profile, profile_revision=self.old_revision, vacancy=self.vacancy,
            matching_config=self.old_config, status=VacancyAnalysis.Status.COMPLETED,
            score=8, completed_at=timezone.now(),
        )

        self.assertIsNone(create_analysis(self.profile, self.vacancy, self.current_config, force=True))
        self.assertEqual(
            create_analysis(self.profile, self.vacancy, self.current_config, include_existing=True),
            completed,
        )
        self.assertEqual(VacancyAnalysis.objects.filter(profile=self.profile, vacancy=self.vacancy).count(), 1)

    def test_each_profile_gets_its_own_analysis(self):
        VacancyAnalysis.objects.create(
            profile=self.profile, profile_revision=self.old_revision, vacancy=self.vacancy,
            matching_config=self.old_config, status=VacancyAnalysis.Status.COMPLETED, score=8,
        )
        other_user = get_user_model().objects.create_user("other-history-owner")
        other = Profile.objects.create(
            owner=other_user, cv_file="profiles/other/cv.pdf", revision_number=1,
        )
        revision = ProfileRevision.objects.create(
            profile=other, version=1, cv_file_path="profiles/other/cv.pdf",
        )

        pending = create_analysis(other, self.vacancy, self.current_config)

        self.assertEqual(pending.profile_revision, revision)
        self.assertEqual(pending.status, VacancyAnalysis.Status.PENDING)
