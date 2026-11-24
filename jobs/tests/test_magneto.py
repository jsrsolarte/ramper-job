from unittest.mock import Mock, patch
from pathlib import Path
from requests import Timeout

from django.test import SimpleTestCase

from jobs.connectors.base import JobListing, SourcePartiallyUnavailable, SourceUnavailable
from jobs.connectors.magneto import MagnetoConnector, validate_magneto_vacancy_url
from jobs.registry import configured_connectors
from profiles.locations import expand_locations


FIXTURES = Path(__file__).parent / "fixtures" / "magneto"
LISTING_URL = "https://www.magneto365.com/co/trabajos/buscar/loc-medellin-antioquia/procesos/ultimos-3-dias"


def fixture(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


class MagnetoParsingTests(SimpleTestCase):
    def setUp(self):
        self.connector = MagnetoConnector()

    def test_listing_cards_extract_title_url_company_contract_and_location(self):
        listings = self.connector.parse(fixture("listing-medellin.html"), LISTING_URL)

        self.assertEqual(len(listings), 1)
        listing = listings[0]
        self.assertEqual(listing.source, "magneto_co")
        self.assertEqual(listing.title, "Analista de procesos (muestra sintética)")
        self.assertEqual(listing.company, "Empresa de prueba")
        self.assertEqual(listing.original_url, "https://www.magneto365.com/co/empleos/vacante-prueba-900001")
        self.assertEqual(listing.location, "Medellín")
        self.assertEqual(listing.contract_type, "Término indefinido")
        self.assertEqual(listing.salary, "$ 2.000.000")
        self.assertEqual(listing.external_id, "")

    def test_optional_fields_missing_and_duplicate_urls_are_handled(self):
        html = fixture("listing-multiple-locations.html")
        duplicated = html.replace("</body>", html.split("<body>", 1)[1].split("</body>", 1)[0] + "</body>")

        listings = self.connector.parse(duplicated, LISTING_URL)

        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].location, "Remoto")
        self.assertIsNone(listings[0].salary)
        self.assertIsNone(listings[0].raw_data.get("publication_label"))

    def test_listing_without_cards_returns_no_results(self):
        self.assertEqual(self.connector.parse("<html><body>Sin resultados</body></html>", LISTING_URL), [])

    def test_detail_extracts_sections_locations_and_salary_provenance(self):
        details = self.connector.parse_detail(fixture("detail.html"), "https://www.magneto365.com/co/empleos/vacante-prueba-900001")

        self.assertEqual(details["title"], "Analista de procesos (ficha sintética)")
        self.assertEqual(details["company"], "Empresa de prueba")
        self.assertEqual(details["canonical_url"], "https://www.magneto365.com/co/empleos/vacante-prueba-900001")
        self.assertEqual(details["locations"], ["Medellín · Antioquia", "Rionegro · Antioquia"])
        self.assertEqual(details["contract_type"], "Obra o labor")
        self.assertEqual(details["employment_type"], "FULL_TIME")
        self.assertEqual(details["requirements"], ["Experiencia y formación de prueba."])
        self.assertEqual(details["responsibilities"], ["Funciones de prueba."])
        self.assertEqual(len(details["salary_observations"]), 3)
        self.assertEqual(details["salary_observations"][-1], {
            "source": "jobposting", "value": {"min": 1838450, "currency": "COP"},
        })

    def test_ambiguous_identity_retains_original_listing_fields(self):
        listing = JobListing(
            source="magneto_co", external_id="", title="Título del listado", company="Empresa de prueba",
            location="Medellín", description=None, original_url="https://www.magneto365.com/co/empleos/listado-1",
        )
        details = {
            "title": "Título incompatible", "company": "Empresa de prueba",
            "canonical_url": "https://www.magneto365.com/co/empleos/ficha-2",
            "locations": ["Rionegro"], "description": "Detalle ajeno",
        }

        merged, confirmed = self.connector.merge_details(listing, details)

        self.assertFalse(confirmed)
        self.assertEqual(merged.title, listing.title)
        self.assertEqual(merged.location, listing.location)
        self.assertIsNone(merged.description)
        self.assertEqual(merged.raw_data["details_fetch"]["status"], "identity_ambiguous")

    def test_external_canonical_url_keeps_detail_unconfirmed(self):
        html = fixture("detail.html").replace(
            'href="https://www.magneto365.com/co/empleos/vacante-prueba-900001"',
            'href="https://example.com/vacante-prueba-900001"',
        )
        details = self.connector.parse_detail(
            html, "https://www.magneto365.com/co/empleos/vacante-prueba-900001"
        )
        listing = JobListing(
            source="magneto_co", external_id="", title="Analista de procesos (ficha sintética)",
            company="Empresa de prueba", location="Medellín", description=None,
            original_url="https://www.magneto365.com/co/empleos/vacante-prueba-900001",
        )

        merged, confirmed = self.connector.merge_details(listing, details)

        self.assertTrue(details["canonical_url_invalid"])
        self.assertFalse(confirmed)
        self.assertIsNone(merged.description)

    def test_conflicting_salary_is_preserved_with_its_sources(self):
        listing = JobListing(
            source="magneto_co", external_id="", title="Mismo título", company="Empresa",
            location="Medellín", description=None, original_url="https://www.magneto365.com/co/empleos/mismo",
            salary="$ 1.000.000",
        )
        details = {
            "title": "Mismo título", "company": "Empresa", "canonical_url": listing.original_url,
            "locations": ["Medellín"], "salary_observations": [
                {"source": "visible", "value": "$ 2.000.000"},
                {"source": "jobposting", "value": {"min": 1_500_000}},
            ],
        }

        merged, confirmed = self.connector.merge_details(listing, details)

        self.assertTrue(confirmed)
        self.assertEqual(merged.salary, "$ 1.000.000")
        self.assertEqual(merged.raw_data["details"]["list_salary"], "$ 1.000.000")
        self.assertEqual(len(merged.raw_data["details"]["salary_observations"]), 2)


class MagnetoUrlValidationTests(SimpleTestCase):
    def test_detail_url_is_normalized(self):
        self.assertEqual(
            validate_magneto_vacancy_url("https://www.magneto365.com/co/empleos/prueba-123/?utm_source=test#section"),
            "https://www.magneto365.com/co/empleos/prueba-123",
        )

    def test_rejects_unsafe_or_non_detail_urls(self):
        for url in (
            "http://www.magneto365.com/co/empleos/prueba",
            "https://example.com/co/empleos/prueba",
            "https://user:password@www.magneto365.com/co/empleos/prueba",
            "https://www.magneto365.com/co/trabajos/buscar/procesos",
            "https://www.magneto365.com/co/empleos/prueba:8443",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_magneto_vacancy_url(url)


class MagnetoSearchAndTransportTests(SimpleTestCase):
    def test_connector_is_registered_with_the_shared_pipeline(self):
        self.assertIn("magneto_co", {connector.source for connector in configured_connectors()})

    def test_search_routes_match_the_two_observed_route_forms(self):
        connector = MagnetoConnector()

        self.assertEqual(
            connector.search_url("Coordinador de"),
            "https://www.magneto365.com/co/trabajos/buscar/ultimos-3-dias/coordinador-de?order=desc_relevance",
        )
        self.assertEqual(
            connector.search_url("Procesos", "Medellín"),
            "https://www.magneto365.com/co/trabajos/buscar/loc-medellin-antioquia/procesos/ultimos-3-dias?order=desc_relevance",
        )
        self.assertEqual(
            connector.search_url("Procesos", "Bogotá"),
            "https://www.magneto365.com/co/trabajos/buscar/loc-bogota-d.c.-bogota-d.c./procesos/ultimos-3-dias?order=desc_relevance",
        )
        for city, slug in (
            ("Bello", "bello-antioquia"),
            ("Envigado", "envigado-antioquia"),
            ("Itagüí", "itagui-antioquia"),
            ("Sabaneta", "sabaneta-antioquia"),
            ("La Estrella", "la-estrella-antioquia"),
            ("Caldas", "caldas-antioquia"),
            ("Copacabana", "copacabana-antioquia"),
            ("Girardota", "girardota-antioquia"),
            ("Barbosa", "barbosa-antioquia"),
            ("Soacha", "soacha-cundinamarca"),
            ("Chía", "chia-cundinamarca"),
            ("Cajicá", "cajica-cundinamarca"),
            ("Cota", "cota-cundinamarca"),
            ("Funza", "funza-cundinamarca"),
            ("Madrid", "madrid-cundinamarca"),
            ("Mosquera", "mosquera-cundinamarca"),
            ("La Calera", "la-calera-cundinamarca"),
            ("Tenjo", "tenjo-cundinamarca"),
            ("Facatativá", "facatativa-cundinamarca"),
            ("Zipaquirá", "zipaquira-cundinamarca"),
        ):
            with self.subTest(city=city):
                self.assertEqual(
                    connector.search_url("Procesos", city),
                    f"https://www.magneto365.com/co/trabajos/buscar/loc-{slug}/procesos-ultimos-3-dias?order=desc_relevance",
                )
        self.assertEqual(
            connector.search_url("  analista   de datos "),
            "https://www.magneto365.com/co/trabajos/buscar/ultimos-3-dias/analista-de-datos?order=desc_relevance",
        )

    def test_unverified_location_route_is_not_guessed(self):
        with self.assertRaisesRegex(ValueError, "(?i)no se ha verificado"):
            MagnetoConnector().search_url("Analista", "Cali")

    def test_profile_expansions_build_a_route_for_every_expanded_location(self):
        connector = MagnetoConnector()
        for profile_location in ("Medellín", "Bogotá D.C."):
            with self.subTest(profile_location=profile_location):
                for city in expand_locations([profile_location]):
                    with self.subTest(city=city):
                        self.assertIn("/loc-", connector.search_url("Procesos", city))

    @patch("jobs.connectors.magneto.socket.getaddrinfo")
    @patch("jobs.connectors.magneto.time.sleep")
    def test_unverified_location_keeps_supported_results_and_marks_query_partial(self, _sleep, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        session = Mock()
        session.get.return_value = Mock(status_code=200, text=fixture("listing-medellin.html"), headers={})
        connector = MagnetoConnector(session=session)

        with self.assertRaises(SourcePartiallyUnavailable) as caught:
            connector.fetch_titles(["Procesos"], ["Medellín", "Cali"])

        self.assertEqual(len(caught.exception.listings), 1)
        session.get.assert_called_once_with(
            connector.search_url("Procesos", "Medellín"),
            headers={"User-Agent": connector.user_agent},
            timeout=(5, 20),
            allow_redirects=False,
        )
        self.assertIn("Cali", connector.status_message)

    @patch("jobs.connectors.magneto.socket.getaddrinfo")
    @patch("jobs.connectors.magneto.time.sleep")
    def test_search_sends_user_agent_and_uses_single_page_per_supported_query(self, _sleep, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        session = Mock()
        session.get.return_value = Mock(status_code=200, text=fixture("listing-medellin.html"), headers={})
        connector = MagnetoConnector(session=session)

        results = connector.fetch_titles(["Procesos"], ["Medellín"])

        self.assertEqual(len(results), 1)
        session.get.assert_called_once()
        self.assertEqual(session.get.call_args.args[0], connector.search_url("Procesos", "Medellín"))
        self.assertEqual(session.get.call_args.kwargs["headers"]["User-Agent"], connector.user_agent)
        self.assertEqual(session.get.call_args.kwargs["timeout"], (5, 20))
        self.assertFalse(session.get.call_args.kwargs["allow_redirects"])

    @patch("jobs.connectors.magneto.socket.getaddrinfo")
    def test_private_dns_result_is_rejected_before_request(self, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("127.0.0.1", 443))]
        session = Mock()
        connector = MagnetoConnector(session=session)

        with self.assertRaises(SourceUnavailable):
            connector.fetch_titles(["procesos"], ["Medellín"])

        session.get.assert_not_called()

    @patch("jobs.connectors.magneto.socket.getaddrinfo")
    def test_redirect_to_unapproved_host_is_rejected(self, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        session = Mock()
        session.get.return_value = Mock(status_code=302, headers={"Location": "https://example.com/"})
        connector = MagnetoConnector(session=session)

        with self.assertRaises(SourceUnavailable):
            connector.fetch_titles(["procesos"], ["Medellín"])

        session.get.assert_called_once()

    @patch("jobs.connectors.magneto.socket.getaddrinfo")
    def test_block_responses_stop_source_without_retry_or_evasion(self, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        for status in (401, 403, 429):
            with self.subTest(status=status):
                session = Mock()
                session.get.return_value = Mock(status_code=status, text="", headers={})
                connector = MagnetoConnector(session=session)

                with self.assertRaises(SourceUnavailable):
                    connector.fetch_titles(["procesos"], ["Medellín"])

                session.get.assert_called_once()

    @patch("jobs.connectors.magneto.socket.getaddrinfo")
    def test_detail_block_returns_partial_listings_without_losing_card_data(self, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        listing = MagnetoConnector().parse(fixture("listing-medellin.html"), LISTING_URL)[0]
        for status in (401, 403, 429):
            with self.subTest(status=status):
                session = Mock()
                session.get.return_value = Mock(status_code=status, text="", headers={})

                with self.assertRaises(SourcePartiallyUnavailable) as caught:
                    MagnetoConnector(session=session).fetch_details([listing, listing])

                self.assertEqual(caught.exception.listings, [listing, listing])
                session.get.assert_called_once()

    @patch("jobs.connectors.magneto.socket.getaddrinfo")
    def test_remote_search_uses_observed_query_without_location(self, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        session = Mock()
        session.get.return_value = Mock(status_code=200, text=fixture("listing-multiple-locations.html"), headers={})
        connector = MagnetoConnector(session=session)

        with self.assertRaises(SourcePartiallyUnavailable) as caught:
            connector.fetch_titles(["analista"], ["Cali"], remote_ok=True)

        session.get.assert_called_once()
        self.assertIn("/buscar/ultimos-3-dias/analista?", session.get.call_args.args[0])
        self.assertIn("no se ha verificado", connector.status_message.lower())
        self.assertEqual(len(caught.exception.listings), 1)

    @patch("jobs.connectors.magneto.socket.getaddrinfo")
    def test_detail_request_uses_user_agent_and_preserves_ambiguous_listing(self, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        listing = MagnetoConnector().parse(fixture("listing-medellin.html"), LISTING_URL)[0]
        session = Mock()
        session.get.return_value = Mock(status_code=200, text=fixture("detail.html"), headers={})
        connector = MagnetoConnector(session=session)

        details = connector.fetch_details([listing])

        self.assertEqual(details[0].title, listing.title)
        self.assertEqual(details[0].location, listing.location)
        self.assertEqual(details[0].raw_data["details_fetch"]["status"], "identity_ambiguous")
        self.assertEqual(session.get.call_args.kwargs["headers"]["User-Agent"], connector.user_agent)

    @patch("jobs.connectors.magneto.socket.getaddrinfo")
    @patch("jobs.connectors.magneto.time.sleep")
    def test_individual_detail_timeout_keeps_its_card_and_continues(self, _sleep, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        first = JobListing(
            source="magneto_co", external_id="", title="Otra vacante", company="Otra empresa",
            location="Medellín", description=None,
            original_url="https://www.magneto365.com/co/empleos/otra-vacante-900002",
        )
        second = JobListing(
            source="magneto_co", external_id="", title="Analista de procesos (ficha sintética)",
            company="Empresa de prueba", location="Medellín", description=None,
            original_url="https://www.magneto365.com/co/empleos/vacante-prueba-900001",
        )
        session = Mock()
        session.get.side_effect = [Timeout("connection timed out"), Mock(
            status_code=200, text=fixture("detail.html"), headers={},
        )]
        connector = MagnetoConnector(session=session)

        listings = connector.fetch_details([first, second])

        self.assertEqual(listings[0], first)
        self.assertEqual(listings[1].raw_data["details_fetch"]["status"], "confirmed")
        self.assertEqual(session.get.call_count, 2)

    @patch("jobs.connectors.magneto.socket.getaddrinfo")
    def test_detail_redirect_limit_is_bounded(self, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        listing = MagnetoConnector().parse(fixture("listing-medellin.html"), LISTING_URL)[0]
        session = Mock()
        session.get.return_value = Mock(
            status_code=302,
            headers={"Location": listing.original_url},
        )
        connector = MagnetoConnector(session=session)

        results = connector.fetch_details([listing])

        self.assertEqual(results[0], listing)
        self.assertEqual(session.get.call_count, connector.max_redirects + 1)
        self.assertIn("demasiadas redirecciones", connector.status_message)
