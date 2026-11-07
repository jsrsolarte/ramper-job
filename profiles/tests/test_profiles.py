from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from profiles.models import Profile, ProfileRevision


class ProfileRevisionTests(TestCase):
    def setUp(self):
        self.first_user = get_user_model().objects.create_user("first", password="LongPass-2026!")
        self.second_user = get_user_model().objects.create_user("second", password="LongPass-2026!")

    def test_profile_updates_create_immutable_revisions(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            upload = SimpleUploadedFile("resume.pdf", b"first cv", content_type="application/pdf")
            self.client.force_login(self.first_user)
            response = self.client.post(
                reverse("profiles:edit"),
                {"search_phrases": "Analista en Bogotá", "locations": "Bogotá", "cv_file": upload},
            )
            self.assertRedirects(response, reverse("profiles:edit"))
            profile = Profile.objects.get(owner=self.first_user)
            first_revision = profile.revisions.get(version=1)

            self.client.post(reverse("profiles:edit"), {"search_phrases": "Líder de datos", "locations": "Bogotá"})
            profile.refresh_from_db()
            self.assertEqual(profile.revision_number, 2)
            self.assertEqual(first_revision.search_phrases, ["Analista en Bogotá"])
            self.assertEqual(first_revision.locations, ["Bogotá"])
            self.assertEqual(profile.revisions.count(), 2)

    @patch("jobs.tasks.refresh_profile_sources.delay")
    @patch("matching.tasks.schedule_profile_analyses.delay")
    def test_profile_update_queues_search_and_analysis_after_commit(self, schedule_analysis, refresh_search):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.client.force_login(self.first_user)
            upload = SimpleUploadedFile("resume.pdf", b"first cv", content_type="application/pdf")
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    reverse("profiles:edit"),
                    {"search_phrases": "Analista de procesos", "locations": "Cali", "cv_file": upload},
                )

        self.assertEqual(response.status_code, 302)
        profile = Profile.objects.get(owner=self.first_user)
        schedule_analysis.assert_called_once_with(profile.pk)
        refresh_search.assert_called_once_with(profile.pk)

    def test_cv_download_is_private_to_its_owner(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.client.force_login(self.first_user)
            upload = SimpleUploadedFile("resume.pdf", b"private resume", content_type="application/pdf")
            self.client.post(reverse("profiles:edit"), {"search_phrases": "", "locations": "", "cv_file": upload})

            self.client.force_login(self.second_user)
            response = self.client.get(reverse("profiles:cv"))
            self.assertEqual(response.status_code, 404)

    @patch("matching.tasks.schedule_eligible_organizations.delay")
    def test_min_score_star_options_save_values_without_revisions_or_reanalysis(self, schedule_organizations):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.client.force_login(self.first_user)
            upload = SimpleUploadedFile("resume.pdf", b"private resume", content_type="application/pdf")
            self.client.post(
                reverse("profiles:edit"),
                {"search_phrases": "", "locations": "", "min_score": "8", "cv_file": upload},
            )
            profile = Profile.objects.get(owner=self.first_user)
            self.assertEqual(profile.min_score, 8)
            self.assertEqual(profile.revisions.count(), 1)

            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(reverse("profiles:edit"), {"search_phrases": "", "locations": "", "min_score": "0"})

        self.assertEqual(response.status_code, 302)
        profile.refresh_from_db()
        self.assertEqual(profile.min_score, 0)
        self.assertEqual(profile.revisions.count(), 1)
        schedule_organizations.assert_not_called()

    def test_min_score_is_rendered_as_accessible_star_options(self):
        self.client.force_login(self.first_user)
        response = self.client.get(reverse("profiles:edit"))

        self.assertContains(response, '<fieldset class="star-select-fieldset" aria-describedby="min-score-help">')
        self.assertContains(response, 'type="radio" id="min-score-0" name="min_score" value="0"')
        self.assertContains(response, 'type="radio" id="min-score-10" name="min_score" value="10"')
        self.assertContains(response, 'aria-label="No descartar vacantes por puntaje"')
        self.assertContains(response, 'aria-label="Descartar automáticamente vacantes nuevas con menos de 10 de 10 puntos, 5 estrellas"')
        self.assertContains(response, 'score-stars')
        self.assertNotContains(response, 'type="range"')
