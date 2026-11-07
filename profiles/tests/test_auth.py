from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class ManagedAccountTests(TestCase):
    def test_staff_can_create_a_family_account_in_admin(self):
        user_model = get_user_model()
        administrator = user_model.objects.create_superuser(
            username="owner",
            email="owner@example.test",
            password="AdminPass-Long-2026!",
        )
        self.client.force_login(administrator)

        response = self.client.post(
            reverse("admin:auth_user_add"),
            {
                "username": "family-member",
                "password1": "FamilyPass-Long-2026!",
                "password2": "FamilyPass-Long-2026!",
                "first_name": "Familiar",
                "last_name": "Ejemplo",
                "email": "family@example.test",
                "is_active": "on",
                "_save": "Guardar",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(user_model.objects.filter(username="family-member").exists())

    def test_public_self_registration_is_not_available(self):
        response = self.client.get("/accounts/signup/")

        self.assertEqual(response.status_code, 404)

    def test_supplied_user_can_sign_in(self):
        get_user_model().objects.create_user(
            username="family-member",
            password="FamilyPass-Long-2026!",
        )

        response = self.client.post(
            reverse("login"),
            {"username": "family-member", "password": "FamilyPass-Long-2026!"},
        )

        self.assertRedirects(response, "/", fetch_redirect_response=False)
