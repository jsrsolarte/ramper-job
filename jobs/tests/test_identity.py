from django.test import SimpleTestCase, TestCase

from jobs.connectors.base import JobListing
from jobs.identity import normalize_vacancy_url, vacancy_dedupe_key
from jobs.models import Vacancy
from jobs.services import save_listing


class VacancyURLIdentityTests(SimpleTestCase):
    def test_tracking_parameters_fragment_host_case_and_trailing_slash_are_normalized(self):
        self.assertEqual(
            normalize_vacancy_url("HTTPS://WWW.Example.test/jobs/123/?utm_source=x#details"),
            "https://www.example.test/jobs/123",
        )

    def test_route_and_source_are_part_of_the_identity(self):
        first = vacancy_dedupe_key("elempleo_co", "123", "Analista", "Empresa", "Bogotá", "https://x.test/jobs/a")
        second = vacancy_dedupe_key("elempleo_co", "123", "Analista", "Empresa", "Bogotá", "https://x.test/jobs/b")
        other_source = vacancy_dedupe_key("computrabajo_co", "123", "Analista", "Empresa", "Bogotá", "https://x.test/jobs/a")
        self.assertNotEqual(first, second)
        self.assertNotEqual(first, other_source)

    def test_invalid_or_credentialed_url_is_rejected(self):
        for url in ("javascript:alert(1)", "https://user:pass@example.test/job", "https:///missing-host"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                normalize_vacancy_url(url)


class VacancyURLPersistenceTests(TestCase):
    def test_same_normalized_url_reuses_row_but_a_distinct_route_does_not(self):
        def listing(url, *, external_id="same-id"):
            return JobListing(
                source="elempleo_co", external_id=external_id, title="Analista", company="Empresa",
                location="Bogotá", description="Descripción", original_url=url,
            )

        first, created = save_listing(listing("https://example.test/jobs/123?tracking=one"))
        same, same_created = save_listing(listing("https://EXAMPLE.test/jobs/123/#detalle"))
        other, other_created = save_listing(listing("https://example.test/jobs/123/edit"))

        self.assertTrue(created)
        self.assertFalse(same_created)
        self.assertTrue(other_created)
        self.assertEqual(first.pk, same.pk)
        self.assertNotEqual(first.pk, other.pk)
        self.assertEqual(Vacancy.objects.count(), 2)
