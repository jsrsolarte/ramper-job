from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class VacancyURLMigrationTests(TransactionTestCase):
    migrate_from = [
        ("jobs", "0008_alter_manualvacancysubmission_source_and_more"),
        ("matching", "0015_aicallattempt_format_action_and_repair_stages"),
        ("dashboard", "0004_vacancyfollowup_archived_at"),
        ("profiles", "0008_profile_min_score_stars"),
    ]
    migrate_to = [
        ("jobs", "0009_vacancy_url_identity_and_detail_state"),
        ("matching", "0015_aicallattempt_format_action_and_repair_stages"),
        ("dashboard", "0004_vacancyfollowup_archived_at"),
        ("profiles", "0008_profile_min_score_stars"),
    ]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        User = old_apps.get_model("auth", "User")
        Profile = old_apps.get_model("profiles", "Profile")
        ProfileRevision = old_apps.get_model("profiles", "ProfileRevision")
        MatchingConfig = old_apps.get_model("matching", "MatchingConfig")
        Vacancy = old_apps.get_model("jobs", "Vacancy")
        VacancyAnalysis = old_apps.get_model("matching", "VacancyAnalysis")
        Discovery = old_apps.get_model("matching", "ProfileVacancyDiscovery")
        FollowUp = old_apps.get_model("dashboard", "VacancyFollowUp")
        Submission = old_apps.get_model("jobs", "ManualVacancySubmission")

        user = User.objects.create_user(username="url-migration-owner")
        profile = Profile.objects.create(owner=user, revision_number=1)
        revision = ProfileRevision.objects.create(profile=profile, version=1)
        config = MatchingConfig.objects.create(version=1, analysis_prompt="", organization_prompt="")
        first = Vacancy.objects.create(
            source="elempleo_co", external_id="123", dedupe_key="a" * 64,
            title="Analista", original_url="https://jobs.example.test/vacancy/123",
        )
        duplicate = Vacancy.objects.create(
            source="elempleo_co", external_id="123", dedupe_key="b" * 64,
            title="Analista", original_url="https://jobs.example.test/vacancy/123?tracking=old",
        )
        self.survivor_id = first.pk
        self.completed_id = VacancyAnalysis.objects.create(
            profile=profile, profile_revision=revision, matching_config=config,
            vacancy=duplicate, status="completed", score=8,
        ).pk
        Discovery.objects.create(profile=profile, vacancy=first, auto_discard_threshold=2)
        Discovery.objects.create(profile=profile, vacancy=duplicate, auto_discard_threshold=3)
        FollowUp.objects.create(profile=profile, vacancy=duplicate, status="applied")
        Submission.objects.create(original_url=duplicate.original_url, vacancy=duplicate)

        MigrationExecutor(connection).migrate(self.migrate_to)

    def tearDown(self):
        MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())
        super().tearDown()

    def test_exact_normalized_collision_preserves_analysis_discovery_follow_up_and_submission(self):
        apps = MigrationExecutor(connection).loader.project_state(self.migrate_to).apps
        Vacancy = apps.get_model("jobs", "Vacancy")
        VacancyAnalysis = apps.get_model("matching", "VacancyAnalysis")
        Discovery = apps.get_model("matching", "ProfileVacancyDiscovery")
        FollowUp = apps.get_model("dashboard", "VacancyFollowUp")
        Submission = apps.get_model("jobs", "ManualVacancySubmission")

        self.assertEqual(Vacancy.objects.count(), 1)
        vacancy = Vacancy.objects.get(pk=self.survivor_id)
        self.assertEqual(vacancy.normalized_url, "https://jobs.example.test/vacancy/123")
        self.assertEqual(vacancy.details_status, "unknown")
        self.assertTrue(VacancyAnalysis.objects.filter(pk=self.completed_id, vacancy=vacancy).exists())
        self.assertEqual(Discovery.objects.count(), 1)
        self.assertEqual(Discovery.objects.get().auto_discard_threshold, 2)
        self.assertEqual(FollowUp.objects.get().status, "applied")
        self.assertEqual(Submission.objects.get().vacancy, vacancy)
