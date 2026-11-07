from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from jobs.models import ManualVacancySubmission, Vacancy


class ManualVacancyAdminViewTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("operator", password="test-password")
        self.applicant = get_user_model().objects.create_user("applicant", password="test-password")
        self.url = reverse("operations:manual_vacancies")
        self.valid_data = {
            "original_url": "https://www.elempleo.com/co/ofertas-trabajo/analista-123",
        }

    def test_admin_can_submit_vacancy_and_web_request_only_enqueues_it(self):
        self.client.force_login(self.admin)

        with patch("operations.views.process_manual_vacancy_submission.delay") as enqueue:
            response = self.client.post(self.url, self.valid_data)

        self.assertRedirects(response, self.url)
        submission = ManualVacancySubmission.objects.get()
        self.assertEqual(submission.status, ManualVacancySubmission.Status.QUEUED)
        self.assertEqual(submission.submitted_by, self.admin)
        self.assertFalse(Vacancy.objects.exists())
        enqueue.assert_called_once_with(submission.pk)

    def test_only_supported_https_vacancy_urls_are_accepted(self):
        self.client.force_login(self.admin)
        invalid_data = {"original_url": "https://example.org/jobs/123"}

        with patch("operations.views.process_manual_vacancy_submission.delay") as enqueue:
            response = self.client.post(self.url, invalid_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "solo se admiten vacantes públicas de El Empleo")
        self.assertFalse(ManualVacancySubmission.objects.exists())
        enqueue.assert_not_called()

    def test_form_exposes_only_the_url_field(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertContains(response, 'name="original_url"')
        self.assertNotContains(response, 'name="title"')
        self.assertNotContains(response, 'name="source"')

    def test_applicant_cannot_view_or_submit_manual_vacancy(self):
        self.client.force_login(self.applicant)

        with patch("operations.views.process_manual_vacancy_submission.delay") as enqueue:
            get_response = self.client.get(self.url)
            post_response = self.client.post(self.url, self.valid_data)

        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(post_response.status_code, 403)
        self.assertFalse(ManualVacancySubmission.objects.exists())
        self.assertFalse(Vacancy.objects.exists())
        enqueue.assert_not_called()

    def test_queue_failure_is_visible_and_recorded(self):
        self.client.force_login(self.admin)

        with patch(
            "operations.views.process_manual_vacancy_submission.delay",
            side_effect=RuntimeError("broker detail must not be shown"),
        ) as enqueue:
            response = self.client.post(self.url, self.valid_data, follow=True)

        submission = ManualVacancySubmission.objects.get()
        self.assertRedirects(response, self.url)
        self.assertEqual(submission.status, ManualVacancySubmission.Status.FAILED)
        self.assertContains(response, "No fue posible poner el registro en cola")
        self.assertNotContains(response, "broker detail")
        enqueue.assert_called_once_with(submission.pk)
