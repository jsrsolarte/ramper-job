import json
import re
import struct

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class ChromeInstallabilityTests(TestCase):
    def test_manifest_is_public_valid_and_has_required_icons(self):
        response = self.client.get("/static/manifest.json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("application/json", response["Content-Type"])
        manifest = json.loads(b"".join(response.streaming_content))
        self.assertEqual(manifest["id"], "/")
        self.assertEqual(manifest["start_url"], "/")
        self.assertEqual(manifest["scope"], "/")
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["name"], "Ramper Job")

        for icon in manifest["icons"]:
            icon_response = self.client.get(icon["src"])
            self.assertEqual(icon_response.status_code, 200)
            self.assertIn("image/png", icon_response["Content-Type"])
            icon_content = b"".join(icon_response.streaming_content)
            width, height = struct.unpack(">II", icon_content[16:24])
            self.assertEqual((width, height), tuple(map(int, icon["sizes"].split("x"))))

    def test_manifest_is_linked_on_login_and_authenticated_pages(self):
        login = self.client.get(reverse("login"))
        self.assertRegex(
            login.content.decode(),
            r'<link rel="manifest" href="/static/manifest(?:\.[a-f0-9]+)?\.json">',
        )

        user = get_user_model().objects.create_user(username="pwa-user", password="test-password")
        self.client.force_login(user)
        home = self.client.get("/")
        self.assertEqual(home.status_code, 200)
        self.assertRegex(
            home.content.decode(),
            r'<link rel="manifest" href="/static/manifest(?:\.[a-f0-9]+)?\.json">',
        )

    def test_private_pages_are_not_cached_and_logout_removes_access(self):
        user = get_user_model().objects.create_user(username="private-user", password="test-password")
        self.client.force_login(user)

        private_page = self.client.get("/")
        self.assertEqual(private_page.status_code, 200)
        self.assertEqual(private_page["Cache-Control"], "private, no-store")

        logout = self.client.post(reverse("logout"))
        self.assertEqual(logout.status_code, 302)
        self.assertEqual(logout["Cache-Control"], "private, no-store")
        self.assertRedirects(self.client.get("/"), f"{reverse('login')}?next=/", fetch_redirect_response=False)

    def test_switching_accounts_opens_only_the_new_account(self):
        user_model = get_user_model()
        first_user = user_model.objects.create_user(
            username="first-account", first_name="Cuenta A", password="test-password"
        )
        second_user = user_model.objects.create_user(
            username="second-account", first_name="Cuenta B", password="test-password"
        )

        self.client.force_login(first_user)
        first_page = self.client.get("/")
        self.assertContains(first_page, "Hola, Cuenta A")
        self.assertEqual(first_page["Cache-Control"], "private, no-store")

        self.client.post(reverse("logout"))
        self.client.force_login(second_user)
        second_page = self.client.get("/")
        self.assertContains(second_page, "Hola, Cuenta B")
        self.assertNotContains(second_page, "Hola, Cuenta A")
        self.assertEqual(second_page["Cache-Control"], "private, no-store")

