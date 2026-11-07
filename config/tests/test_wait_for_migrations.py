from io import StringIO
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase


class WaitForMigrationsCommandTests(TestCase):
    def test_returns_when_all_migrations_are_applied(self):
        output = StringIO()

        call_command("wait_for_migrations", stdout=output, timeout=1, interval=0.01)

        self.assertIn("Todas las migraciones están aplicadas.", output.getvalue())

    @patch("operations.management.commands.wait_for_migrations.time.sleep")
    @patch("operations.management.commands.wait_for_migrations.time.monotonic", side_effect=[0, 0, 1])
    @patch("operations.management.commands.wait_for_migrations.MigrationExecutor")
    def test_times_out_while_migrations_remain_pending(self, executor_class, _monotonic, _sleep):
        executor_class.return_value.migration_plan.return_value = [object()]

        with self.assertRaisesMessage(CommandError, "todavía tiene migraciones pendientes"):
            call_command("wait_for_migrations", timeout=0.5, interval=0.1)
