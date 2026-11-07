from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from dashboard.models import VacancyFollowUp
from dashboard.tasks import archive_inactive_follow_ups, discard_stale_recommendations
from jobs.models import Vacancy
from matching.models import RUBRIC_VERSION, MatchingConfig, VacancyAnalysis
from operations.models import OperationalParameter
from operations.parameters import AUTO_DISCARD_DAYS_KEY, FOLLOW_UP_ARCHIVE_DAYS_KEY
from profiles.models import Profile


class ConfigurableRetentionTaskTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("retention-owner")
        self.profile = Profile.objects.create(owner=self.user, revision_number=1)
        self.revision = self.profile.revisions.create(version=1)
        self.config = MatchingConfig.objects.create(
            version=1,
            rubric_version=RUBRIC_VERSION,
            analysis_prompt="Prompt",
            organization_prompt="Organiza",
        )

    def create_analysis(self, slug, *, completed_days_ago=8):
        vacancy = Vacancy.objects.create(
            source="elempleo_co",
            title=f"Vacante {slug}",
            original_url=f"https://jobs.example.test/{slug}",
        )
        analysis = VacancyAnalysis.objects.create(
            profile=self.profile,
            profile_revision=self.revision,
            vacancy=vacancy,
            matching_config=self.config,
            status=VacancyAnalysis.Status.COMPLETED,
            score=8,
            score_breakdown={"skills": {"score": 4}},
            completed_at=timezone.now() - timedelta(days=completed_days_ago),
        )
        return vacancy, analysis

    def test_discard_uses_the_current_setting_and_the_seven_day_default(self):
        vacancy, _analysis = self.create_analysis("discard-setting")

        OperationalParameter.objects.create(key=AUTO_DISCARD_DAYS_KEY, value=9)
        result = discard_stale_recommendations.run()
        self.assertEqual(result["discarded"], 0)
        self.assertFalse(VacancyFollowUp.objects.filter(profile=self.profile, vacancy=vacancy).exists())

        OperationalParameter.objects.filter(key=AUTO_DISCARD_DAYS_KEY).update(value=7)
        result = discard_stale_recommendations.run()
        follow_up = VacancyFollowUp.objects.get(profile=self.profile, vacancy=vacancy)
        self.assertEqual(result["discarded"], 1)
        self.assertEqual(follow_up.status, VacancyFollowUp.Status.DISCARDED)

    def test_invalid_discard_setting_falls_back_to_seven_days(self):
        vacancy, _analysis = self.create_analysis("discard-invalid-setting")
        OperationalParameter.objects.create(key=AUTO_DISCARD_DAYS_KEY, value=0)

        result = discard_stale_recommendations.run()

        self.assertEqual(result["discarded"], 1)
        self.assertEqual(
            VacancyFollowUp.objects.get(profile=self.profile, vacancy=vacancy).status,
            VacancyFollowUp.Status.DISCARDED,
        )

    def test_archive_uses_the_current_setting_and_the_thirty_day_default(self):
        vacancy, _analysis = self.create_analysis("archive-setting", completed_days_ago=1)
        follow_up = VacancyFollowUp.objects.create(
            profile=self.profile,
            vacancy=vacancy,
            status=VacancyFollowUp.Status.APPLIED,
            state_changed_at=timezone.now() - timedelta(days=31),
        )

        OperationalParameter.objects.create(key=FOLLOW_UP_ARCHIVE_DAYS_KEY, value=32)
        result = archive_inactive_follow_ups.run()
        self.assertEqual(result["archived"], 0)
        follow_up.refresh_from_db()
        self.assertIsNone(follow_up.archived_at)

        OperationalParameter.objects.filter(key=FOLLOW_UP_ARCHIVE_DAYS_KEY).update(value=30)
        result = archive_inactive_follow_ups.run()
        follow_up.refresh_from_db()
        self.assertEqual(result["archived"], 1)
        self.assertIsNotNone(follow_up.archived_at)

    def test_daily_archiving_discards_expired_recommendations_before_archiving(self):
        vacancy, _analysis = self.create_analysis("discard-before-archive", completed_days_ago=8)

        result = archive_inactive_follow_ups.run()

        follow_up = VacancyFollowUp.objects.get(profile=self.profile, vacancy=vacancy)
        self.assertEqual(result["archived"], 0)
        self.assertEqual(follow_up.status, VacancyFollowUp.Status.DISCARDED)
        self.assertIsNone(follow_up.archived_at)
        self.assertGreater(follow_up.state_changed_at, timezone.now() - timedelta(minutes=1))

    def test_both_daily_tasks_remain_scheduled_in_order(self):
        discard = settings.CELERY_BEAT_SCHEDULE["discard-stale-recommendations"]
        archive = settings.CELERY_BEAT_SCHEDULE["archive-inactive-follow-ups"]

        self.assertEqual(discard["task"], "dashboard.tasks.discard_stale_recommendations")
        self.assertEqual(archive["task"], "dashboard.tasks.archive_inactive_follow_ups")
        self.assertLess(discard["schedule"]._orig_minute, archive["schedule"]._orig_minute)
