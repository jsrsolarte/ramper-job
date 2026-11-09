from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class GuidedTourCompletionMigrationTests(TransactionTestCase):
    migrate_from = ("profiles", "0005_guidedtourprogress")
    migrate_to = ("profiles", "0006_guidedtourprogress_mandatory_completed")

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        historical_apps = executor.loader.project_state([self.migrate_from]).apps
        User = historical_apps.get_model(*settings.AUTH_USER_MODEL.split("."))
        self.previous_user_id = User.objects.create(
            username="previous-user",
            password="!",
            last_login=timezone.now(),
        ).pk
        self.first_login_user_id = User.objects.create(
            username="first-login-user",
            password="!",
            last_login=None,
        ).pk
        self.admin_user_id = User.objects.create(
            username="previous-admin",
            password="!",
            last_login=timezone.now(),
            is_staff=True,
            is_superuser=True,
        ).pk

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        self.apps_after_migration = executor.loader.project_state([self.migrate_to]).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_only_previous_aspirants_are_migrated_as_exempt(self):
        Progress = self.apps_after_migration.get_model("profiles", "GuidedTourProgress")

        previous_progress = Progress.objects.get(owner_id=self.previous_user_id)
        first_login_progress = Progress.objects.filter(owner_id=self.first_login_user_id).first()

        self.assertTrue(previous_progress.mandatory_completed)
        self.assertTrue(first_login_progress is None or not first_login_progress.mandatory_completed)
        self.assertFalse(Progress.objects.filter(owner_id=self.admin_user_id).exists())
