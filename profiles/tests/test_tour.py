from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from profiles.models import GuidedTourProgress, Profile
from profiles.tour import TOUR_STEPS


class GuidedTourProgressTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.applicant = user_model.objects.create_user("applicant", password="LongPassword-2026!")
        self.other_applicant = user_model.objects.create_user("other-applicant", password="LongPassword-2026!")
        self.admin = user_model.objects.create_superuser(
            "platform-admin", email="admin@example.test", password="LongPassword-2026!"
        )

    def test_initial_state_is_offered_without_creating_a_progress_record(self):
        self.client.force_login(self.applicant)

        response = self.client.get(reverse("profiles:tour_state"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], GuidedTourProgress.Status.NOT_STARTED)
        self.assertTrue(response.json()["offer"])
        self.assertEqual(response.json()["step_count"], len(TOUR_STEPS))
        self.assertFalse(GuidedTourProgress.objects.exists())

    def test_start_next_previous_close_and_reopen_persist_the_current_step(self):
        self.client.force_login(self.applicant)

        started = self.client.post(reverse("profiles:tour_action"), {"action": "start"})
        self.assertEqual(started.status_code, 200)
        self.assertEqual(started.json()["step"]["id"], "open_profile")
        self.assertEqual(started.json()["version"], 3)

        advanced = self.client.post(
            reverse("profiles:tour_action"),
            {"action": "next", "step": "not-a-valid-step", "next_url": "https://example.test/"},
        )
        self.assertEqual(advanced.json()["step"]["id"], "cv")
        self.assertEqual(advanced.json()["step"]["url"], reverse("profiles:edit"))
        moved_back = self.client.post(reverse("profiles:tour_action"), {"action": "previous"})
        self.assertEqual(moved_back.json()["step"]["id"], "open_profile")

        closed = self.client.post(reverse("profiles:tour_action"), {"action": "close"})
        self.assertEqual(closed.json()["status"], GuidedTourProgress.Status.IN_PROGRESS)
        progress = GuidedTourProgress.objects.get(owner=self.applicant)
        self.assertEqual(progress.current_step, "open_profile")
        self.assertEqual(progress.status, GuidedTourProgress.Status.IN_PROGRESS)
        self.assertEqual(self.client.get(reverse("profiles:tour_state")).json()["step"]["id"], "open_profile")

        reopened = self.client.post(reverse("profiles:tour_action"), {"action": "reopen"})
        self.assertEqual(reopened.json()["step"]["id"], "open_profile")
        self.assertEqual(GuidedTourProgress.objects.count(), 1)

    def test_last_step_completes_and_manual_reopen_starts_from_the_beginning(self):
        self.client.force_login(self.applicant)
        self.client.post(reverse("profiles:tour_action"), {"action": "start"})
        for _step in TOUR_STEPS[:-1]:
            response = self.client.post(reverse("profiles:tour_action"), {"action": "next"})
            self.assertEqual(response.status_code, 200)

        completed = self.client.post(reverse("profiles:tour_action"), {"action": "next"})
        self.assertEqual(completed.json()["status"], GuidedTourProgress.Status.COMPLETED)
        self.assertIsNone(completed.json()["step"])
        self.assertFalse(completed.json()["offer"])

        restarted = self.client.post(reverse("profiles:tour_action"), {"action": "reopen"})
        self.assertEqual(restarted.json()["status"], GuidedTourProgress.Status.IN_PROGRESS)
        self.assertEqual(restarted.json()["step"]["id"], "open_profile")

    def test_skip_is_persisted_and_does_not_open_a_tour(self):
        self.client.force_login(self.applicant)

        skipped = self.client.post(reverse("profiles:tour_action"), {"action": "skip"})

        self.assertEqual(skipped.status_code, 200)
        self.assertEqual(skipped.json()["status"], GuidedTourProgress.Status.SKIPPED)
        self.assertIsNone(skipped.json()["step"])
        self.assertFalse(skipped.json()["offer"])

    def test_progress_is_isolated_between_applicants(self):
        GuidedTourProgress.objects.create(
            owner=self.applicant,
            status=GuidedTourProgress.Status.IN_PROGRESS,
            current_step="phrases",
        )
        self.client.force_login(self.other_applicant)

        response = self.client.post(reverse("profiles:tour_action"), {"action": "next"})

        self.assertEqual(response.status_code, 409)
        self.assertFalse(GuidedTourProgress.objects.filter(owner=self.other_applicant).exists())
        self.assertEqual(
            GuidedTourProgress.objects.get(owner=self.applicant).current_step,
            "phrases",
        )

    def test_progress_steps_route_across_profile_and_dashboard_pages(self):
        self.client.force_login(self.applicant)
        response = self.client.post(reverse("profiles:tour_action"), {"action": "start"})
        self.assertEqual(response.json()["step"]["id"], "open_profile")
        self.assertEqual(response.json()["step"]["url"], reverse("dashboard:home"))

        response = self.client.post(reverse("profiles:tour_action"), {"action": "next"})
        self.assertEqual(response.json()["step"]["id"], "cv")
        self.assertEqual(response.json()["step"]["url"], reverse("profiles:edit"))

        for _step in TOUR_STEPS[1:6]:
            response = self.client.post(reverse("profiles:tour_action"), {"action": "next"})

        self.assertEqual(response.json()["step"]["id"], "return_to_vacancies")
        self.assertEqual(response.json()["step"]["url"], reverse("profiles:edit"))

        response = self.client.post(reverse("profiles:tour_action"), {"action": "next"})
        self.assertEqual(response.json()["step"]["id"], "stars")
        self.assertEqual(response.json()["step"]["url"], reverse("dashboard:home"))
        response = self.client.post(reverse("profiles:tour_action"), {"action": "next"})
        self.assertEqual(response.json()["step"]["id"], "details")
        self.assertEqual(response.json()["step"]["url"], reverse("dashboard:home"))
        response = self.client.post(reverse("profiles:tour_action"), {"action": "next"})
        self.assertEqual(response.json()["step"]["id"], "follow_up")
        self.assertEqual(response.json()["step"]["url"], reverse("dashboard:home"))
        response = self.client.post(reverse("profiles:tour_action"), {"action": "next"})
        self.assertEqual(response.json()["step"]["id"], "pending")
        self.assertEqual(response.json()["step"]["url"], reverse("dashboard:pending"))
        self.assertEqual(self.client.get(reverse("profiles:tour_state")).json()["step"]["url"], reverse("dashboard:pending"))

    def test_administrators_cannot_read_or_create_tour_progress(self):
        self.client.force_login(self.admin)

        state = self.client.get(reverse("profiles:tour_state"))
        action = self.client.post(reverse("profiles:tour_action"), {"action": "start"})

        self.assertEqual(state.status_code, 404)
        self.assertEqual(action.status_code, 404)
        self.assertFalse(GuidedTourProgress.objects.exists())

    def test_other_staff_accounts_are_also_excluded(self):
        staff = get_user_model().objects.create_user(
            "support-staff", password="LongPassword-2026!", is_staff=True
        )
        self.client.force_login(staff)

        response = self.client.get(reverse("profiles:tour_state"))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(GuidedTourProgress.objects.exists())

    def test_profile_preferences_are_not_changed_by_tour_actions(self):
        profile = Profile.objects.create(
            owner=self.applicant,
            search_phrases=["Analista de procesos"],
            locations=["Medellín"],
            remote_ok=True,
            min_score=6,
        )
        self.client.force_login(self.applicant)

        for action in ("start", "next", "next", "close", "reopen", "skip"):
            self.client.post(reverse("profiles:tour_action"), {"action": action})

        profile.refresh_from_db()
        self.assertEqual(profile.search_phrases, ["Analista de procesos"])
        self.assertEqual(profile.locations, ["Medellín"])
        self.assertTrue(profile.remote_ok)
        self.assertEqual(profile.min_score, 6)

    def test_invalid_actions_and_get_mutations_are_rejected(self):
        self.client.force_login(self.applicant)

        invalid = self.client.post(reverse("profiles:tour_action"), {"action": "goto"})
        get_mutation = self.client.get(reverse("profiles:tour_action"))

        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(get_mutation.status_code, 405)


class GuidedTourPresentationTests(TestCase):
    def setUp(self):
        self.applicant = get_user_model().objects.create_user("tour-user", password="LongPassword-2026!")
        self.client.force_login(self.applicant)

    def test_profile_and_dashboard_expose_stable_tour_destinations(self):
        profile_page = self.client.get(reverse("profiles:edit"))
        self.assertContains(profile_page, 'data-tour="cv"')
        self.assertContains(profile_page, 'data-tour="phrases"')
        self.assertContains(profile_page, 'data-tour="locations"')
        self.assertContains(profile_page, 'data-tour="remote"')
        self.assertContains(profile_page, 'data-tour="threshold"')
        self.assertContains(profile_page, 'data-tour="back-to-dashboard"')

        pending_page = self.client.get(reverse("dashboard:pending"))
        self.assertContains(pending_page, 'data-tour="pending-tab"')
        self.assertContains(pending_page, 'data-tour="follow-up-tabs"')
        self.assertContains(pending_page, 'data-tour="profile-nav"')

    def test_recommendation_filter_and_details_have_tour_destinations(self):
        Profile.objects.create(owner=self.applicant, cv_file="profiles/1/cv/v1.pdf")

        response = self.client.get(reverse("dashboard:home"))

        self.assertContains(response, 'data-tour="score-filter"')
        self.assertContains(response, 'data-tour="dashboard-content"')
        home_template = Path(settings.BASE_DIR, "dashboard/templates/dashboard/home.html").read_text()
        self.assertIn('data-tour="vacancy-details"', home_template)

    def test_tour_copy_covers_profile_controls_filters_analysis_and_tracking_tabs(self):
        copy_by_step = {step["id"]: step["text"] for step in TOUR_STEPS}
        self.assertIn("CV", copy_by_step["cv"])
        self.assertIn("frases", copy_by_step["phrases"])
        self.assertIn("ubicaciones", copy_by_step["locations"])
        self.assertIn("remotas", copy_by_step["remote"])
        self.assertIn("Descartadas", copy_by_step["threshold"])
        self.assertIn("Cero desactiva", copy_by_step["threshold"])
        self.assertIn("ya encontradas", copy_by_step["threshold"])
        self.assertIn("Por analizar", copy_by_step["pending"])
        self.assertIn("Mi perfil", copy_by_step["open_profile"])
        self.assertIn("regresar", copy_by_step["return_to_vacancies"])
        self.assertIn("Aplicadas", copy_by_step["follow_up"])
        self.assertIn("En proceso", copy_by_step["follow_up"])
        self.assertIn("Entrevista", copy_by_step["follow_up"])
        self.assertIn("Finalizadas", copy_by_step["follow_up"])
        self.assertIn("Descartadas", copy_by_step["follow_up"])
        self.assertIn("estrellas", copy_by_step["stars"])
        self.assertIn("no cambia el umbral", copy_by_step["stars"])
        self.assertIn("detalles", copy_by_step["details"])
        self.assertIn("por qué coincide", copy_by_step["details"])
        self.assertIn("aspectos", copy_by_step["details"])

    def test_guide_controls_are_keyboard_accessible_and_not_shown_to_admins(self):
        response = self.client.get(reverse("profiles:edit"))
        self.assertContains(response, 'role="dialog"')
        self.assertContains(response, 'aria-modal="false"')
        self.assertContains(response, 'aria-live="polite"')
        self.assertContains(response, 'aria-label="Cerrar la guía y continuar después"')
        self.assertContains(response, 'data-tour-action="previous"')
        self.assertContains(response, 'data-tour-action="next"')
        self.assertContains(response, 'data-tour-action="skip"')
        self.assertContains(response, 'data-tour-reopen')
        tour_script = Path(settings.BASE_DIR, "static/tour.js").read_text()
        app_styles = Path(settings.BASE_DIR, "static/app.css").read_text()
        self.assertIn('event.key === "Escape"', tour_script)
        self.assertIn("nextButton.focus()", tour_script)
        self.assertIn("returnFocus.focus()", tour_script)
        self.assertIn("@media (max-width: 640px)", app_styles)
        self.assertIn("prefers-reduced-motion", app_styles)

        self.client.force_login(get_user_model().objects.create_superuser(
            "tour-admin", email="tour-admin@example.test", password="LongPassword-2026!"
        ))
        admin_response = self.client.get(reverse("operations:admin_center"))
        self.assertNotContains(admin_response, 'data-tour-reopen')
        self.assertNotContains(admin_response, 'id="guided-tour"')


class GuidedTourCSRFSecurityTests(TestCase):
    def test_action_requires_a_valid_csrf_token(self):
        applicant = get_user_model().objects.create_user("csrf-applicant", password="LongPassword-2026!")
        client = Client(enforce_csrf_checks=True)
        client.force_login(applicant)

        denied = client.post(reverse("profiles:tour_action"), {"action": "start"})
        self.assertEqual(denied.status_code, 403)
        self.assertFalse(GuidedTourProgress.objects.exists())

        client.get(reverse("profiles:edit"))
        token = client.cookies["csrftoken"].value
        accepted = client.post(
            reverse("profiles:tour_action"),
            {"action": "start"},
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(accepted.status_code, 200)
        self.assertTrue(GuidedTourProgress.objects.filter(owner=applicant).exists())
