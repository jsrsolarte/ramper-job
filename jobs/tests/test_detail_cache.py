from django.test import TestCase

from jobs.connectors.base import JobListing, mark_details_confirmed
from jobs.models import Vacancy, VacancyDetailLease
from jobs.services import (
    claim_detail_fetch,
    confirmed_listing_details,
    release_detail_fetch_leases,
    save_listing,
)


class VacancyDetailCacheTests(TestCase):
    def listing(self, url="https://example.test/jobs/known", **overrides):
        values = {
            "source": "elempleo_co", "external_id": "42", "title": "Analista",
            "company": "Empresa", "location": "Bogotá", "description": "Descripción del listado",
            "original_url": url,
        }
        values.update(overrides)
        return JobListing(**values)

    def test_only_confirmed_detail_data_is_reused(self):
        stored = self.listing(description="Descripción completa", salary="$5 millones")
        vacancy, _ = save_listing(mark_details_confirmed(stored))

        cached = confirmed_listing_details(self.listing(description="Texto corto"))

        self.assertIsNotNone(cached)
        self.assertEqual(cached.description, "Descripción completa")
        self.assertEqual(cached.salary, "$5 millones")
        self.assertEqual(vacancy.details_status, Vacancy.DetailStatus.CONFIRMED)

    def test_listing_data_alone_is_not_a_confirmed_detail(self):
        save_listing(self.listing())

        self.assertIsNone(confirmed_listing_details(self.listing()))

    def test_detail_fetch_lease_serializes_same_url_and_can_be_released(self):
        state, first_token = claim_detail_fetch("elempleo_co", self.listing().original_url, token="first")
        busy_state, busy_token = claim_detail_fetch("elempleo_co", self.listing().original_url, token="second")
        release_detail_fetch_leases(token=first_token, url_hashes=[VacancyDetailLease.objects.get().normalized_url_hash])
        resumed_state, resumed_token = claim_detail_fetch("elempleo_co", self.listing().original_url, token="second")

        self.assertEqual((state, first_token), ("claimed", "first"))
        self.assertEqual((busy_state, busy_token), ("busy", ""))
        self.assertEqual((resumed_state, resumed_token), ("claimed", "second"))

    def test_search_card_does_not_overwrite_confirmed_detail_fields(self):
        save_listing(mark_details_confirmed(self.listing(description="Detalle completo", salary="$4 millones")))

        vacancy, _ = save_listing(self.listing(description="Descripción resumida", salary=None))

        self.assertEqual(vacancy.description, "Detalle completo")
        self.assertEqual(vacancy.salary, "$4 millones")
