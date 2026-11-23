from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from profiles.tests.helpers import mark_tour_completed


class PrimaryNavigationTests(TestCase):
    def test_applicant_can_open_recommendations_from_main_navigation(self):
        applicant = get_user_model().objects.create_user("navigation-applicant", password="test-password")
        mark_tour_completed(applicant)
        self.client.force_login(applicant)

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-label="Navegación principal"')
        self.assertContains(response, 'href="/?state=pending" aria-current="page">Recomendaciones</a>')
        self.assertContains(response, 'href="/perfil/" data-tour="profile-nav">Mi perfil</a>')

    def test_administrators_do_not_see_applicant_recommendations_link(self):
        admin = get_user_model().objects.create_superuser(
            "navigation-admin",
            email="navigation-admin@example.test",
            password="test-password",
        )
        self.client.force_login(admin)

        response = self.client.get(reverse("operations:admin_center"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administración")
        self.assertNotContains(response, "Recomendaciones")
