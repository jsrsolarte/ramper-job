from django.test import TestCase
from django.utils import timezone

from jobs.connectors.base import JobListing
from jobs.models import Vacancy
from jobs.services import save_listing, save_listings


class VacancyNormalizationTests(TestCase):
    def test_save_listings_classifies_distinct_vacancies_and_material_changes(self):
        unchanged = JobListing(
            source="elempleo_co", external_id="991", title="Analista",
            company="Empresa", location="Medellín", description="Descripción",
            original_url="https://example.test/known-unchanged",
        )
        updated = JobListing(
            source="elempleo_co", external_id="992", title="Analista",
            company="Empresa", location="Medellín", description="Descripción",
            original_url="https://example.test/known-updated",
        )
        save_listing(unchanged)
        save_listing(updated)

        result = save_listings([
            unchanged,
            JobListing(
                source="elempleo_co", external_id="992", title="Analista",
                company="Empresa", location="Medellín", description="Nueva descripción",
                original_url="https://example.test/known-updated",
            ),
            JobListing(
                source="elempleo_co", external_id="993", title="Ingeniera",
                company="Empresa", location="Medellín", description="Vacante nueva",
                original_url="https://example.test/brand-new",
            ),
            unchanged,
        ])

        self.assertEqual(len(result.vacancies), 3)
        self.assertEqual(result.new_count, 1)
        self.assertEqual(result.known_count, 2)
        self.assertEqual(result.known_updated_count, 1)
        self.assertEqual(result.known_unchanged_count, 1)

    def test_publicly_observed_listing_marks_availability_active(self):
        listing = JobListing(
            source="elempleo_co", external_id="observed-job", title="Analista",
            company="Empresa", location="Medellín", description="Descripción",
            original_url="https://example.test/observed-job",
        )

        vacancy, _ = save_listing(listing)

        self.assertEqual(vacancy.availability_status, Vacancy.AvailabilityStatus.ACTIVE)

    def test_date_only_publication_from_structured_details_is_saved(self):
        listing = JobListing(
            source="elempleo_co", external_id="job-date", title="Analista",
            company="Empresa", location="Medellín", description="Descripción",
            original_url="https://example.test/job-date",
            raw_data={"details": {"date_posted": "2026-10-29"}},
        )

        vacancy, _ = save_listing(listing)

        self.assertEqual(timezone.localtime(vacancy.published_at).date().isoformat(), "2026-10-29")

    def test_unknown_fields_remain_empty_and_source_url_is_preserved(self):
        listing = JobListing(
            source="elempleo_co",
            external_id="job-1",
            title="Desarrolladora Python",
            company=None,
            location=None,
            description="Experiencia con Django.",
            original_url="https://www.elempleo.com/co/ofertas-trabajo/python-1?tracking=abc",
        )

        vacancy, created = save_listing(listing)

        self.assertTrue(created)
        self.assertEqual(vacancy.original_url, "https://www.elempleo.com/co/ofertas-trabajo/python-1")
        self.assertIsNone(vacancy.company)
        self.assertIsNone(vacancy.location)
        self.assertEqual(vacancy.description, "Experiencia con Django.")

    def test_structured_details_and_list_salary_are_preserved_independently(self):
        listing = JobListing(
            source="elempleo_co", external_id="job-2", title="Ingeniero industrial",
            company="Empresa", location="Bogotá · Av. 68 # 13-50", description="Descripción completa",
            original_url="https://www.elempleo.com/co/ofertas-trabajo/job-2",
            raw_data={"details": {"version": 1, "list_salary": "$4 a $4,5 millones",
                                  "salary_periodicity": "mensuales", "city": "Bogotá",
                                  "address": "Av. 68 # 13-50", "modality": "presencial"}},
            salary="$4.214.000 pagos mensuales", contract_type="Obra o labor",
        )

        vacancy, _ = save_listing(listing)

        self.assertEqual(vacancy.salary, "$4.214.000 pagos mensuales")
        self.assertEqual(vacancy.contract_type, "Obra o labor")
        self.assertEqual(vacancy.raw_data["details"]["list_salary"], "$4 a $4,5 millones")
        self.assertEqual(vacancy.raw_data["details"]["salary_periodicity"], "mensuales")
        self.assertEqual(vacancy.raw_data["details"]["city"], "Bogotá")

    def test_empty_refresh_details_do_not_erase_previously_known_values(self):
        initial = JobListing(
            source="elempleo_co", external_id="job-3", title="Analista", company="Empresa",
            location="Envigado", description="Descripción", original_url="https://example.test/job-3",
            raw_data={"details": {"version": 1, "city": "Envigado", "salary_periodicity": "mensual"}},
            salary="$3.000.000 mensual", contract_type="Indefinido",
        )
        vacancy, _ = save_listing(initial)
        sparse = JobListing(
            source="elempleo_co", external_id="job-3", title="Analista", company=None,
            location=None, description=None, original_url="https://example.test/job-3",
            raw_data={"details": {"version": 1, "city": None, "salary_periodicity": None}},
        )

        updated, _ = save_listing(sparse)

        self.assertEqual(updated.location, "Envigado")
        self.assertEqual(updated.salary, "$3.000.000 mensual")
        self.assertEqual(updated.contract_type, "Indefinido")
        self.assertEqual(updated.raw_data["details"]["city"], "Envigado")
        self.assertEqual(updated.raw_data["details"]["salary_periodicity"], "mensual")

    def test_same_source_job_with_changed_url_reuses_vacancy_and_tracks_alternate_url(self):
        first = JobListing(
            source="elempleo_co", external_id="12345", title="Analista de procesos",
            company="Empresa", location="Soacha", description="Descripción",
            original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-12345",
        )
        second = JobListing(
            source="elempleo_co", external_id="12345", title="Analista de procesos",
            company="Empresa", location="Soacha", description="Actualización",
            original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-procesos-12345",
        )

        original, created = save_listing(first)
        repeated, created_again = save_listing(second)

        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(Vacancy.objects.count(), 1)
        self.assertEqual(repeated.pk, original.pk)
        self.assertEqual(repeated.original_url, first.original_url)
        self.assertEqual(repeated.raw_data["alternate_urls"], [second.original_url])
        self.assertEqual(repeated.description, "Actualización")

    def test_fingerprint_reuses_vacancy_when_source_has_no_stable_numeric_id(self):
        first = JobListing(
            source="elempleo_co", external_id="analista-de-procesos", title="Analista de procesos",
            company="Empresa Ejemplo", location="Bogotá D.C.", description=None,
            original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-procesos-a",
        )
        second = JobListing(
            source="elempleo_co", external_id="analista-procesos-2", title="ANALÍSTA DE PROCESOS",
            company="Empresa Ejemplo", location="Bogota D.C.", description=None,
            original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-procesos-b",
        )

        saved_first, created = save_listing(first)
        saved_second, created_again = save_listing(second)

        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(Vacancy.objects.filter(source="elempleo_co").count(), 1)
        self.assertEqual(saved_second.pk, saved_first.pk)
