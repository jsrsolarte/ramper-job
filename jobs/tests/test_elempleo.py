from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from jobs.connectors.base import SourceUnavailable
from jobs.connectors.elempleo import ElempleoConnector, validate_elempleo_vacancy_url


class ElempleoConnectorTests(SimpleTestCase):
    def test_url_validator_allows_only_https_elempleo_vacancy_pages(self):
        self.assertEqual(
            validate_elempleo_vacancy_url("https://www.elempleo.com/co/ofertas-trabajo/analista-123?utm=x"),
            "https://www.elempleo.com/co/ofertas-trabajo/analista-123",
        )
        for url in (
            "http://www.elempleo.com/co/ofertas-trabajo/analista-123",
            "https://example.org/co/ofertas-trabajo/analista-123",
            "https://www.elempleo.com/co/ofertas-empleo/trabajo-analista",
            "https://user@www.elempleo.com/co/ofertas-trabajo/analista-123",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_elempleo_vacancy_url(url)

    @patch("jobs.connectors.elempleo.socket.getaddrinfo")
    def test_direct_url_fetch_extracts_structured_vacancy_fields(self, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        html = '''<html><body><main><h1>Analista de procesos</h1>
          <p>Salario: $4 millones</p><p>Tipo de contrato: Indefinido</p>
          <p>Lugar: Medellín presencial</p><p>Mejora continua</p></main></body></html>'''
        session = Mock()
        session.get.return_value = Mock(status_code=200, text=html, headers={})

        listing = ElempleoConnector(session=session).fetch_vacancy_url(
            "https://www.elempleo.com/co/ofertas-trabajo/analista-123"
        )

        self.assertEqual(listing.title, "Analista de procesos")
        self.assertEqual(listing.source, "elempleo_co")
        self.assertEqual(listing.location, "Medellín")
        self.assertEqual(listing.salary, "$4 millones")
        self.assertEqual(listing.contract_type, "Indefinido")
        self.assertEqual(listing.raw_data["details"]["modality"], "presencial")
        session.get.assert_called_once()

    @patch("jobs.connectors.elempleo.socket.getaddrinfo")
    def test_private_dns_result_is_rejected_before_request(self, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("127.0.0.1", 443))]
        session = Mock()

        with self.assertRaises(SourceUnavailable):
            ElempleoConnector(session=session).fetch_vacancy_url(
                "https://www.elempleo.com/co/ofertas-trabajo/analista-123"
            )

        session.get.assert_not_called()

    @patch("jobs.connectors.elempleo.socket.getaddrinfo")
    def test_redirect_to_unapproved_host_is_rejected_without_following_it(self, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        session = Mock()
        session.get.return_value = Mock(
            status_code=302, headers={"Location": "http://127.0.0.1/admin"}, text=""
        )

        with self.assertRaises(ValueError):
            ElempleoConnector(session=session).fetch_vacancy_url(
                "https://www.elempleo.com/co/ofertas-trabajo/analista-123"
            )

        session.get.assert_called_once()

    def test_parser_extracts_public_job_links_and_available_fields(self):
        html = """
        <html><body>
          <article class="vacancy-card">
            <a href="/co/ofertas-trabajo/analista-datos-12345">Vacante: Analista de datos</a>
            <div>Trabaja en Empresa Ejemplo</div><div>Bogotá</div>
            <p>Publicado hoy</p><p>Experiencia en SQL y análisis.</p>
          </article>
          <a href="/co/iniciar-sesion">Iniciar sesión</a>
        </body></html>
        """
        jobs = ElempleoConnector(listing_url="https://www.elempleo.com/co/ofertas-empleo/").parse(html)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].external_id, "12345")
        self.assertEqual(jobs[0].title, "Analista de datos")
        self.assertEqual(jobs[0].company, "Empresa Ejemplo")
        self.assertIn("Experiencia en SQL", jobs[0].description)
        self.assertEqual(jobs[0].raw_data["publication_label"], "hoy")

    def test_parser_reads_structured_job_postings(self):
        html = '''<script type="application/ld+json">
        {"@type":"JobPosting","title":"Ingeniera","url":"/co/ofertas-trabajo/ingeniera-87",
         "hiringOrganization":{"name":"Acme"},"jobLocation":{"address":{"addressLocality":"Cali"}},
         "description":"<p>Diseño de sistemas</p>","datePosted":"2026-10-29T10:30:00-05:00"}
        </script>'''
        jobs = ElempleoConnector(listing_url="https://www.elempleo.com/co/ofertas-empleo/").parse(html)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].company, "Acme")
        self.assertEqual(jobs[0].location, "Cali")
        self.assertEqual(jobs[0].description, "Diseño de sistemas")
        self.assertEqual(jobs[0].raw_data["datePosted"], "2026-10-29T10:30:00-05:00")

    def test_detail_parser_extracts_structured_conditions_and_keeps_original_text(self):
        html = """<html><body><main>
          <h1>Ingeniero/a industrial procesos de mejoramiento y calidad</h1>
          <p>Salario: $4.214.000 pagos mensuales</p>
          <p>Tipo de contrato: Obra o labor por licencia de maternidad</p>
          <p>Lugar: Bogotá Av. 68 # 13-50 presencial</p>
          <p>1 año de experiencia Experiencia mínima</p><p>Universitaria Nivel educativo</p>
          <p>Calidad Área laboral</p><p>Horario: Lunes a viernes administrativo</p>
          <p>20 Vacantes Número de vacantes</p>
          <h2>Responsabilidades</h2><p>Mejorar procesos de calidad.</p>
          <h2>Conocimientos técnicos</h2><p>Sistemas de Gestión de Calidad</p>
          <h2>Requisitos:</h2><p>Nivel académico: profesional en Ingeniería industrial</p>
        </main></body></html>"""

        details = ElempleoConnector().parse_detail(html)

        self.assertEqual(details["salary_text"], "$4.214.000 pagos mensuales")
        self.assertEqual(details["salary_periodicity"], "mensuales")
        self.assertEqual(details["city"], "Bogotá")
        self.assertEqual(details["address"], "Av. 68 # 13-50")
        self.assertEqual(details["modality"], "presencial")
        self.assertEqual(details["contract_type"], "Obra o labor por licencia de maternidad")
        self.assertEqual(details["experience"], "1 año")
        self.assertEqual(details["education"], "Universitaria")
        self.assertEqual(details["area"], "Calidad")
        self.assertEqual(details["schedule"], "Lunes a viernes administrativo")
        self.assertEqual(details["vacancy_count"], "20")
        self.assertIn("Mejorar procesos de calidad", " ".join(details["responsibilities"]))
        self.assertIn("Sistemas de Gestión de Calidad", " ".join(details["requirements"]))
        self.assertIn("Ingeniería industrial", " ".join(details["requirements"]))

    def test_detail_merge_keeps_list_salary_and_falls_back_for_missing_fields(self):
        from jobs.connectors.base import JobListing

        listing = JobListing(
            "elempleo_co", "1886786534", "Ingeniero industrial", "Empresa", "Medellín",
            "Texto del listado", "https://www.elempleo.com/co/ofertas-trabajo/job-1",
            {"publication_label": "hoy"}, salary="$4 a $4,5 millones",
        )
        enriched = ElempleoConnector._merge_listing_details(
            listing,
            {"version": 1, "salary_text": "$4.214.000 pagos mensuales", "city": "Bogotá",
             "address": "Av. 68 # 13-50", "modality": "presencial", "description": "Detalle completo"},
        )

        self.assertEqual(enriched.location, "Bogotá · Av. 68 # 13-50")
        self.assertEqual(enriched.description, "Detalle completo")
        self.assertEqual(enriched.salary, "$4.214.000 pagos mensuales")
        self.assertEqual(enriched.raw_data["details"]["list_salary"], "$4 a $4,5 millones")
        self.assertEqual(enriched.raw_data["publication_label"], "hoy")

    def test_detail_parser_tolerates_missing_fields_and_label_variants(self):
        details = ElempleoConnector().parse_detail(
            "<main><p>Ubicación: Envigado, Antioquia</p><p>Experiencia requerida: 2 años</p>"
            "<p>Modalidad de trabajo: Híbrido</p></main>"
        )

        self.assertEqual(details["city"], "Envigado")
        self.assertEqual(details["experience"], "2 años")
        self.assertEqual(details["modality"], "Híbrido")
        self.assertIsNone(details["salary_text"])
        self.assertIsNone(details["contract_type"])

    def test_detail_parser_recognizes_all_configured_nearby_city_names(self):
        details = ElempleoConnector().parse_detail(
            "<main><p>Lugar: La Estrella Calle 80 # 50-10 presencial</p></main>"
        )

        self.assertEqual(details["city"], "La Estrella")
        self.assertEqual(details["address"], "Calle 80 # 50-10")

    def test_detail_failure_keeps_listing_data_and_does_not_fail_batch(self):
        listing_html = """<article><a href="/co/ofertas-trabajo/analista-123">Analista de procesos</a>
          <p>Trabaja en Empresa Ejemplo</p><p>Medellín</p><p>Publicado hoy</p>
          <p>Mejora continua</p></article>"""
        session = Mock()
        session.get.side_effect = [
            Mock(status_code=200, text=listing_html, url="https://www.elempleo.com/co/ofertas-empleo/trabajo-analista"),
            Mock(status_code=503, text="", url="https://www.elempleo.com/co/ofertas-trabajo/analista-123"),
        ]
        connector = ElempleoConnector(session=session)

        results = connector.fetch(["analista"])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].location, "Medellín")
        self.assertIn("Mejora continua", results[0].description)
        self.assertIn("HTTP 503", connector.status_message)

    def test_authentication_or_rate_limit_stops_source_fetch(self):
        session = Mock()
        session.get.return_value.status_code = 403
        connector = ElempleoConnector(session=session)

        with self.assertRaises(SourceUnavailable):
            connector.fetch(["procesos"])

    def test_public_source_http_failure_is_reported_as_unavailable(self):
        session = Mock()
        session.get.return_value.status_code = 503
        connector = ElempleoConnector(session=session)

        with self.assertRaises(SourceUnavailable):
            connector.fetch(["procesos"])

    def test_search_url_uses_elempleo_keyword_slug(self):
        connector = ElempleoConnector(listing_url="https://www.elempleo.com/co/ofertas-empleo/")

        self.assertEqual(
            connector.search_url("  Analista de procesos "),
            "https://www.elempleo.com/co/ofertas-empleo/trabajo-analista-de-procesos?PublishDate=hoy",
        )

    def test_search_url_combines_keyword_city_and_recent_filter(self):
        connector = ElempleoConnector(listing_url="https://www.elempleo.com/co/ofertas-empleo/")

        self.assertEqual(
            connector.search_url("procesos", "Soacha"),
            "https://www.elempleo.com/co/ofertas-empleo/soacha/trabajo-procesos?PublishDate=hoy",
        )

    def test_listing_card_salary_range_is_extracted_without_becoming_detail_salary(self):
        html = """<article><a href="/co/ofertas-trabajo/analista-123">Analista</a>
          <p>$4 a $4,5 millones</p></article>"""

        jobs = ElempleoConnector().parse(html, "https://www.elempleo.com/co/ofertas-empleo/trabajo-analista")

        self.assertEqual(jobs[0].salary, "$4 a $4,5 millones")

    @patch("jobs.connectors.elempleo.time.sleep")
    def test_fetch_combines_searches_and_deduplicates_duplicate_links(self, sleep):
        html = """<article class="vacancy-card">
          <a href="/co/ofertas-trabajo/analista-123">Analista de procesos</a>
          <p>Mejora continua</p></article>"""
        session = Mock()
        session.get.side_effect = [
            Mock(status_code=200, text=html, url="https://www.elempleo.com/co/ofertas-empleo/trabajo-procesos"),
            Mock(status_code=200, text=html, url="https://www.elempleo.com/co/ofertas-empleo/trabajo-analista"),
            Mock(status_code=200, text="<main><p>Detalle</p></main>", url="https://www.elempleo.com/co/ofertas-trabajo/analista-123"),
        ]
        connector = ElempleoConnector(session=session)

        results = connector.fetch(["procesos", "analista"])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].original_url, "https://www.elempleo.com/co/ofertas-trabajo/analista-123")
        self.assertEqual(
            [entry.args[0] for entry in session.get.call_args_list],
            [
                "https://www.elempleo.com/co/ofertas-empleo/trabajo-procesos?PublishDate=hoy",
                "https://www.elempleo.com/co/ofertas-empleo/trabajo-analista?PublishDate=hoy",
                "https://www.elempleo.com/co/ofertas-trabajo/analista-123",
            ],
        )
        self.assertEqual(sleep.call_count, 2)

    @patch("jobs.connectors.elempleo.time.sleep")
    def test_fetch_uses_each_location_and_deduplicates_overlapping_results(self, sleep):
        html = '<a href="/co/ofertas-trabajo/analista-123">Analista de procesos</a>'
        session = Mock()
        session.get.side_effect = [
            Mock(status_code=200, text=html, url="https://www.elempleo.com/co/ofertas-empleo/medellin/trabajo-analista"),
            Mock(status_code=200, text=html, url="https://www.elempleo.com/co/ofertas-empleo/itagui/trabajo-analista"),
            Mock(status_code=200, text="<main><p>Detalle</p></main>", url="https://www.elempleo.com/co/ofertas-trabajo/analista-123"),
        ]
        connector = ElempleoConnector(session=session)

        results = connector.fetch(["analista"], locations=["Medellín", "Itagüí"])

        self.assertEqual(len(results), 1)
        self.assertEqual(
            [entry.args[0] for entry in session.get.call_args_list],
            [
                "https://www.elempleo.com/co/ofertas-empleo/medellin/trabajo-analista?PublishDate=hoy",
                "https://www.elempleo.com/co/ofertas-empleo/itagui/trabajo-analista?PublishDate=hoy",
                "https://www.elempleo.com/co/ofertas-trabajo/analista-123",
            ],
        )
        self.assertEqual(sleep.call_count, 2)

    def test_recent_window_keeps_today_and_yesterday_labels_but_drops_older_dates(self):
        from jobs.connectors.base import JobListing
        from datetime import timedelta
        from django.utils import timezone

        def listing(label):
            return JobListing("elempleo_co", "job-1", "Analista", "Empresa", "Bogotá", None,
                              "https://elempleo.com/co/ofertas-trabajo/a", {"publication_label": label})

        self.assertTrue(ElempleoConnector._within_recent_window(listing("Hoy")))
        self.assertTrue(ElempleoConnector._within_recent_window(listing("Ayer")))
        self.assertFalse(ElempleoConnector._within_recent_window(listing("Hace 1 semana")))

    def test_exact_publication_time_uses_a_24_hour_window(self):
        from datetime import timedelta
        from django.utils import timezone
        from jobs.connectors.base import JobListing

        now = timezone.now()
        def listing(published_at):
            return JobListing("elempleo_co", "job-1", "Analista", "Empresa", "Bogotá", None,
                              "https://elempleo.com/co/ofertas-trabajo/a", {"datePosted": published_at.isoformat()})

        with patch("jobs.connectors.elempleo.timezone.now", return_value=now):
            self.assertTrue(ElempleoConnector._within_recent_window(listing(now - timedelta(hours=23))))
            self.assertFalse(ElempleoConnector._within_recent_window(listing(now - timedelta(hours=25))))

    def test_fetch_continues_when_one_keyword_fails_and_reports_partial_status(self):
        html = '<a href="/co/ofertas-trabajo/analista-123">Analista de procesos</a>'
        session = Mock()
        session.get.side_effect = [
            Mock(status_code=503, text="", url=""),
            Mock(status_code=200, text=html, url="https://www.elempleo.com/co/ofertas-empleo/trabajo-analista"),
            Mock(status_code=200, text="<main><p>Detalle</p></main>", url="https://www.elempleo.com/co/ofertas-trabajo/analista-123"),
        ]
        connector = ElempleoConnector(session=session)

        results = connector.fetch(["procesos", "analista"])

        self.assertEqual(len(results), 1)
        self.assertIn("HTTP 503", connector.status_message)

    def test_empty_keywords_do_not_trigger_general_search(self):
        session = Mock()
        connector = ElempleoConnector(session=session)

        self.assertEqual(connector.fetch([]), [])
        session.get.assert_not_called()

    def test_blocking_response_stops_remaining_keyword_queries(self):
        session = Mock()
        session.get.return_value = Mock(status_code=429, text="", url="")
        connector = ElempleoConnector(session=session)

        with self.assertRaises(SourceUnavailable):
            connector.fetch(["procesos", "analista"])

        session.get.assert_called_once()
