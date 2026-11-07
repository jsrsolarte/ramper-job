from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class VacancyIdentityMigrationTests(TransactionTestCase):
    migrate_from = [
        ("jobs", "0002_jobsourcestatus"),
        ("matching", "0003_profile_search_and_structured_description"),
        ("profiles", "0003_profile_search_and_structured_description"),
    ]
    migrate_to = [
        ("jobs", "0003_vacancy_identity_and_publication_date"),
        ("matching", "0003_profile_search_and_structured_description"),
        ("profiles", "0003_profile_search_and_structured_description"),
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

        user = User.objects.create_user(username="migration-owner")
        profile = Profile.objects.create(owner=user, revision_number=1)
        revision = ProfileRevision.objects.create(profile=profile, version=1)
        config = MatchingConfig.objects.create(version=1, analysis_prompt="", organization_prompt="")
        first = Vacancy.objects.create(
            source="elempleo_co", external_id="123", title="Analista de procesos", company="Empresa",
            location="Soacha", original_url="https://jobs.example.test/vacancy/123",
        )
        second = Vacancy.objects.create(
            source="elempleo_co", external_id="123", title="Analista de procesos", company="Empresa",
            location="Soacha", original_url="https://jobs.example.test/vacancy/123?tracking=1",
        )
        completed = VacancyAnalysis.objects.create(
            profile=profile, profile_revision=revision, matching_config=config, vacancy=first,
            status="completed", score=91,
        )
        VacancyAnalysis.objects.create(
            profile=profile, profile_revision=revision, matching_config=config, vacancy=second,
            status="pending", score=None,
        )
        self.completed_analysis_id = completed.pk
        self.survivor_id = first.pk

        MigrationExecutor(connection).migrate(self.migrate_to)

    def tearDown(self):
        MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())
        super().tearDown()

    def test_duplicate_vacancies_and_analyses_are_consolidated(self):
        apps = MigrationExecutor(connection).loader.project_state(self.migrate_to).apps
        Vacancy = apps.get_model("jobs", "Vacancy")
        VacancyAnalysis = apps.get_model("matching", "VacancyAnalysis")

        self.assertEqual(Vacancy.objects.count(), 1)
        vacancy = Vacancy.objects.get(pk=self.survivor_id)
        self.assertIn("https://jobs.example.test/vacancy/123?tracking=1", vacancy.raw_data["alternate_urls"])
        self.assertEqual(vacancy.analyses.count(), 1)
        self.assertTrue(VacancyAnalysis.objects.filter(pk=self.completed_analysis_id, vacancy=vacancy, score=91).exists())
