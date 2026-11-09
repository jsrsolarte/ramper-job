import re
from datetime import timedelta
from urllib.parse import unquote
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from operations.models import AdminAuditEvent
from profiles.models import Profile


class AdminCenterAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser("owner", password="strong-admin-pass")
        self.applicant = User.objects.create_user("candidate", password="strong-applicant-pass")

    def test_only_one_platform_superuser_can_exist(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                get_user_model().objects.create_superuser("second-owner", password="strong-pass")

    def test_admin_can_open_center_and_applicant_is_denied(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("operations:admin_center"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestionar usuarios")

        self.client.force_login(self.applicant)
        response = self.client.get(reverse("operations:admin_center"))
        self.assertEqual(response.status_code, 403)


class UserManagementTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser("owner", password="strong-admin-pass")
        self.applicant = User.objects.create_user(
            "candidate", password="strong-applicant-pass", email="candidate@example.test",
        )
        self.client.force_login(self.admin)

    def test_admin_creates_non_admin_account_and_audit_event(self):
        response = self.client.post(reverse("operations:create_user"), {
            "username": "new-candidate",
            "email": "new-candidate@example.test",
            "password1": "Candidate-pass-2026!",
            "password2": "Candidate-pass-2026!",
        })

        self.assertRedirects(response, reverse("operations:users"))
        new_user = get_user_model().objects.get(username="new-candidate")
        self.assertFalse(new_user.is_staff)
        self.assertFalse(new_user.is_superuser)
        audit = AdminAuditEvent.objects.get(target=new_user)
        self.assertEqual(audit.actor, self.admin)
        self.assertEqual(audit.action, AdminAuditEvent.Action.ACCOUNT_CREATED)

    def test_deactivate_and_reactivate_preserve_profile_and_audit_actor(self):
        profile = Profile.objects.create(
            owner=self.applicant, search_phrases=["analista de datos"], locations=["Medellín"],
        )

        response = self.client.post(reverse("operations:toggle_user", args=[self.applicant.pk]), {"active": "false"})
        self.assertRedirects(response, reverse("operations:users"))
        self.applicant.refresh_from_db()
        self.assertFalse(self.applicant.is_active)
        self.assertEqual(Profile.objects.get(owner=self.applicant).pk, profile.pk)

        response = self.client.post(reverse("operations:toggle_user", args=[self.applicant.pk]), {"active": "true"})
        self.assertRedirects(response, reverse("operations:users"))
        self.applicant.refresh_from_db()
        self.assertTrue(self.applicant.is_active)
        events = list(AdminAuditEvent.objects.filter(target=self.applicant).order_by("created_at"))
        self.assertEqual([event.action for event in events], [
            AdminAuditEvent.Action.ACCOUNT_DEACTIVATED,
            AdminAuditEvent.Action.ACCOUNT_REACTIVATED,
        ])
        self.assertTrue(all(event.actor == self.admin for event in events))

    def test_applicant_cannot_list_create_or_change_accounts(self):
        self.client.force_login(self.applicant)
        protected_requests = [
            self.client.get(reverse("operations:users")),
            self.client.post(reverse("operations:create_user"), {"username": "intruder"}),
            self.client.post(reverse("operations:toggle_user", args=[self.applicant.pk]), {"active": "false"}),
            self.client.post(reverse("operations:toggle_user", args=[999999]), {"active": "false"}),
            self.client.post(reverse("operations:request_password_reset", args=[self.applicant.pk])),
        ]

        self.assertEqual([response.status_code for response in protected_requests], [403] * len(protected_requests))
        self.assertEqual(get_user_model().objects.count(), 2)
        self.assertFalse(AdminAuditEvent.objects.exists())

    @override_settings(PASSWORD_RESET_TIMEOUT=300)
    def test_admin_generates_one_time_link_without_email_or_password_disclosure(self):
        self.applicant.email = ""
        self.applicant.save(update_fields=("email",))
        with patch("django.core.mail.send_mail") as send_mail, self.assertNoLogs("operations.views", level="DEBUG"):
            response = self.client.post(reverse("operations:request_password_reset", args=[self.applicant.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "operations/password_reset_link.html")
        send_mail.assert_not_called()
        self.assertContains(response, "Copiar enlace")
        self.assertNotIn("candidate@example.test", response.content.decode())
        self.assertNotContains(response, "New-candidate-pass-2026!")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["Referrer-Policy"], "no-referrer")
        event = AdminAuditEvent.objects.get(target=self.applicant)
        self.assertEqual(event.action, AdminAuditEvent.Action.PASSWORD_RESET_LINK_GENERATED)

        match = re.search(
            r"/accounts/password-reset/confirm/([^/\s\"<>]+)/([^/\s\"<>]+)",
            response.content.decode(),
        )
        self.assertIsNotNone(match)
        uidb64, token = (unquote(part) for part in match.groups())
        uid = urlsafe_base64_decode(uidb64).decode()
        self.assertEqual(uid, str(self.applicant.pk))
        self.assertTrue(default_token_generator.check_token(self.applicant, token))

        confirm_url = reverse("password_reset_confirm", kwargs={"uidb64": uidb64, "token": token})
        initial_confirmation = self.client.get(confirm_url)
        self.assertEqual(initial_confirmation.status_code, 302)
        completion = self.client.post(initial_confirmation["Location"], {
            "new_password1": "New-candidate-pass-2026!",
            "new_password2": "New-candidate-pass-2026!",
        })
        self.assertEqual(completion.status_code, 302)
        self.applicant.refresh_from_db()
        self.assertTrue(self.applicant.check_password("New-candidate-pass-2026!"))
        self.assertFalse(default_token_generator.check_token(self.applicant, token))

    def test_inactive_account_cannot_receive_a_reset_link(self):
        self.applicant.is_active = False
        self.applicant.save(update_fields=("is_active",))

        response = self.client.post(reverse("operations:request_password_reset", args=[self.applicant.pk]))

        self.assertRedirects(response, reverse("operations:users"))
        self.assertEqual(
            AdminAuditEvent.objects.get(target=self.applicant).action,
            AdminAuditEvent.Action.PASSWORD_RESET_UNAVAILABLE,
        )

    def test_link_becomes_invalid_if_account_is_deactivated_after_generation(self):
        response = self.client.post(reverse("operations:request_password_reset", args=[self.applicant.pk]))
        match = re.search(
            r"/accounts/password-reset/confirm/([^/\s\"<>]+)/([^/\s\"<>]+)",
            response.content.decode(),
        )
        self.assertIsNotNone(match)
        uidb64, token = (unquote(part) for part in match.groups())

        self.applicant.is_active = False
        self.applicant.save(update_fields=("is_active",))

        confirm_url = reverse("password_reset_confirm", kwargs={"uidb64": uidb64, "token": token})
        confirmation = self.client.get(confirm_url)
        self.assertEqual(confirmation.status_code, 200)
        self.assertContains(confirmation, "El enlace ya no es válido")

    @override_settings(PASSWORD_RESET_TIMEOUT=60)
    def test_password_reset_token_expires(self):
        token = default_token_generator.make_token(self.applicant)
        expired_time = timezone.now().replace(tzinfo=None) + timedelta(seconds=61)

        with patch("django.contrib.auth.tokens.PasswordResetTokenGenerator._now", return_value=expired_time):
            self.assertFalse(default_token_generator.check_token(self.applicant, token))
            uidb64 = urlsafe_base64_encode(str(self.applicant.pk).encode())
            confirm_url = reverse("password_reset_confirm", kwargs={"uidb64": uidb64, "token": token})
            confirmation = self.client.get(confirm_url)
        self.assertContains(confirmation, "El enlace ya no es válido")
