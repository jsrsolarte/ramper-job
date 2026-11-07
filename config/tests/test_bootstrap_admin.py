from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase


class BootstrapPlatformAdminTests(TestCase):
    def run_interactive_bootstrap(self, username="stage-admin", email="admin@example.test", password="Valid-test-pass-839!"):
        output = StringIO()
        with (
            patch("sys.stdin") as stdin,
            patch("builtins.input", side_effect=[username, email]),
            patch("getpass.getpass", side_effect=[password, password]),
        ):
            stdin.isatty.return_value = True
            call_command("bootstrap_platform_admin", stdout=output)
        return output.getvalue(), password

    def test_creates_admin_with_hidden_password_and_never_echoes_it(self):
        output, password = self.run_interactive_bootstrap()

        admin = get_user_model().objects.get(username="stage-admin")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.check_password(password))
        self.assertNotIn(password, output)
        self.assertIn("Cuenta administradora creada.", output)

    def test_second_run_refuses_to_create_another_admin(self):
        get_user_model().objects.create_superuser("existing-admin", password="Existing-test-pass-829!")

        with self.assertRaisesMessage(CommandError, "Ya existe una cuenta administradora"):
            call_command("bootstrap_platform_admin")

        self.assertEqual(get_user_model().objects.filter(is_superuser=True).count(), 1)

    def test_requires_interactive_terminal_before_prompting_for_secrets(self):
        with patch("sys.stdin") as stdin, patch("builtins.input") as prompt:
            stdin.isatty.return_value = False
            with self.assertRaisesMessage(CommandError, "requiere una terminal interactiva"):
                call_command("bootstrap_platform_admin")
        prompt.assert_not_called()
