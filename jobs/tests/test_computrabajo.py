from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from jobs.connectors.base import SourcePartiallyUnavailable, SourceUnavailable
from jobs.connectors.computrabajo import ComputrabajoConnector, validate_computrabajo_url
from jobs.registry import configured_connectors
from jobs.search_groups import group_search_requests
from jobs.tasks import SourceFetchSummary, _fetch_source_listings, _record_source_fetch_outcome
from operations.models import OperationalRun


SEARCH_HTML = """<div id="offersGridOfferContainer">
<article class="box_offer sel" data-id="8C01929719760B8D61373E686DCF3405">
<h2><a class="js-o-link fc_base" href="/ofertas-de-trabajo/oferta-de-trabajo-analista-de-procesos-123#lc=track">Analista de Procesos y Transformación / Medellín</a></h2>
<p class="dFlex"><a offer-grid-article-company-url="">COMPLEMENTOS HUMANOS</a></p>
<p class="fs16 fc_base mt5"><span>Medellín, Antioquia</span></p>
<div class="fs13 mt15"><span class="dIB mr10"><span class="icon i_salary"></span>$ 5.369.000,00 (Mensual)</span></div>
<p class="fs13 fc_aux mt15">Hace 44 minutos</p>
</article>
<a href="?pubdate=1&amp;p=2&amp;by=relevance">Siguiente</a>
</div>"""

DETAIL_HTML = """<main><h1>Analista de Procesos y Transformación</h1>
<div><p class="fwB fs16 mbB">Resumen</p><p>$ 5.500.000 (Mensual)</p>
<p>Contrato de Obra o labor</p><p>Medellín</p><p>Presencial</p></div>
<p class="fwB fs16 mbB">Descripción de la oferta</p>
<div class="fs16 t_word_wrap" data-testid="offer-description">Objetivo del cargo: mejorar procesos.<br>Ubicación: Medellín</div>
<h3>Requisitos</h3><p>Profesional en Ingeniería Industrial</p>
<h3>Principales funciones</h3><p>Optimizar procesos internos</p></main>"""


class ComputrabajoConnectorTests(SimpleTestCase):
    def test_search_url_normalizes_accents_spaces_and_uses_first_page_params(self):
        connector = ComputrabajoConnector()

        self.assertEqual(
            connector.search_url("  analista   de procesos ", "Medellín"),
            "https://co.computrabajo.com/trabajo-de-analista-de-procesos-en-medellin?pubdate=1&p=1&by=relevance",
        )
        self.assertIn("/trabajo-de-analista-de-procesos?", connector.search_url("analista de procesos"))
        self.assertNotIn("p=2", connector.search_url("analista de procesos"))

    def test_listing_parser_extracts_public_card_fields_and_discards_tracking_fragment(self):
        connector = ComputrabajoConnector()

        listings = connector.parse(SEARCH_HTML, "https://co.computrabajo.com/trabajo-de-analista-en-medellin")

        self.assertEqual(len(listings), 1)
        listing = listings[0]
        self.assertEqual(listing.external_id, "8C01929719760B8D61373E686DCF3405")
        self.assertEqual(listing.title, "Analista de Procesos y Transformación / Medellín")
        self.assertEqual(listing.company, "COMPLEMENTOS HUMANOS")
        self.assertEqual(listing.location, "Medellín, Antioquia")
        self.assertEqual(listing.salary, "$ 5.369.000,00 (Mensual)")
        self.assertEqual(listing.raw_data["publication_label"], "Hace 44 minutos")
        self.assertEqual(listing.original_url, "https://co.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-analista-de-procesos-123")

    def test_listing_parser_deduplicates_repeated_external_ids(self):
        card_start = SEARCH_HTML.index("<article")
        card_end = SEARCH_HTML.index("</article>") + len("</article>")
        card = SEARCH_HTML[card_start:card_end]
        duplicate = SEARCH_HTML.replace("</article>\n<a href", f"</article>\n{card}\n<a href", 1)
        listings = ComputrabajoConnector().parse(duplicate, "https://co.computrabajo.com/trabajo-de-analista")

        self.assertEqual(len(listings), 1)

    def test_listing_parser_accepts_incomplete_cards(self):
        listings = ComputrabajoConnector().parse(
            '<article class="box_offer"><a class="js-o-link" href="/ofertas-de-trabajo/job">Auxiliar</a></article>',
            "https://co.computrabajo.com/trabajo-de-auxiliar",
        )

        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].external_id, "")
        self.assertIsNone(listings[0].company)
        self.assertIsNone(listings[0].location)
        self.assertIsNone(listings[0].salary)

    @patch("jobs.connectors.computrabajo.socket.getaddrinfo")
    @patch("jobs.connectors.computrabajo.time.sleep")
    def test_user_agent_is_sent_to_search_and_detail(self, _sleep, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        session = Mock()
        session.get.side_effect = [
            Mock(status_code=200, text=SEARCH_HTML, headers={}),
            Mock(status_code=200, text=DETAIL_HTML, headers={}),
        ]
        connector = ComputrabajoConnector(session=session)

        titles = connector.fetch_titles(["analista"], ["Medellín"])
        details = connector.fetch_details(titles)

        self.assertEqual(len(details), 1)
        self.assertEqual(session.get.call_args_list[0].kwargs["headers"]["User-Agent"], connector.user_agent)
        self.assertEqual(session.get.call_args_list[1].kwargs["headers"]["User-Agent"], connector.user_agent)
        self.assertEqual(session.get.call_args_list[0].kwargs["timeout"], (5, 20))
        self.assertFalse(session.get.call_args_list[1].kwargs["allow_redirects"])
        self.assertEqual(details[0].salary, "$ 5.500.000 (Mensual)")
        self.assertEqual(details[0].raw_data["details"]["listing_salary"], "$ 5.369.000,00 (Mensual)")
        self.assertEqual(details[0].raw_data["details"]["requirements"], ["Profesional en Ingeniería Industrial"])

    @patch("jobs.connectors.computrabajo.socket.getaddrinfo")
    @patch("jobs.connectors.computrabajo.time.sleep")
    def test_detail_blocks_keep_listing_data_and_stop_remaining_detail_requests(self, _sleep, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        first = ComputrabajoConnector().parse(SEARCH_HTML, "https://co.computrabajo.com/trabajo-de-analista")[0]
        second = first.__class__(**{**first.__dict__, "external_id": "another", "original_url": first.original_url + "-other"})
        for status in (401, 403, 429):
            with self.subTest(status=status):
                session = Mock()
                session.get.return_value = Mock(status_code=status, text="", headers={})
                connector = ComputrabajoConnector(session=session)

                with self.assertRaises(SourcePartiallyUnavailable) as caught:
                    connector.fetch_details([first, second])

                self.assertEqual(caught.exception.listings[0].salary, first.salary)
                self.assertEqual(len(caught.exception.listings), 2)
                session.get.assert_called_once()
                self.assertIn("bloqueó", connector.status_message)

    @patch("jobs.connectors.computrabajo.socket.getaddrinfo")
    @patch("jobs.connectors.computrabajo.time.sleep")
    def test_temporary_detail_failure_keeps_card_and_fetches_each_unique_url_once(self, _sleep, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        listing = ComputrabajoConnector().parse(SEARCH_HTML, "https://co.computrabajo.com/trabajo-de-analista")[0]
        session = Mock()
        session.get.return_value = Mock(status_code=503, text="", headers={})
        connector = ComputrabajoConnector(session=session)

        results = connector.fetch_details([listing, listing])

        self.assertEqual(results, [listing, listing])
        self.assertIn("HTTP 503", connector.status_message)
        session.get.assert_called_once()

    @patch("jobs.connectors.computrabajo.socket.getaddrinfo")
    @patch("jobs.connectors.computrabajo.time.sleep")
    def test_search_block_stops_remaining_location_requests(self, _sleep, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        session = Mock()
        session.get.return_value = Mock(status_code=429, text="", headers={})
        connector = ComputrabajoConnector(session=session)

        with self.assertRaises(SourceUnavailable):
            connector.fetch_titles(["analista"], ["Medellín", "Envigado"])

        session.get.assert_called_once()

    @patch("matching.services.preselect_listing_titles")
    @patch("jobs.connectors.computrabajo.socket.getaddrinfo")
    @patch("jobs.connectors.computrabajo.time.sleep")
    def test_search_block_keeps_prior_cards_and_skips_all_detail_requests(self, sleep, getaddrinfo, preselect):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        card = ComputrabajoConnector().parse(SEARCH_HTML, "https://co.computrabajo.com/trabajo-de-analista")[0]
        preselect.return_value = SimpleNamespace(listings=[card], discarded_count=0, input_tokens=0)
        session = Mock()
        session.get.side_effect = [
            Mock(status_code=200, text=SEARCH_HTML, headers={}),
            Mock(status_code=403, text="", headers={}),
        ]
        connector = ComputrabajoConnector(session=session)

        summary = _fetch_source_listings(connector, ["analista"], ["Medellín", "Envigado"], remote_ok=False)

        self.assertEqual(summary.listings, [card])
        self.assertFalse(summary.source_available)
        self.assertEqual(summary.details_requested_count, 0)
        self.assertEqual(session.get.call_count, 2)
        sleep.assert_called_once_with(0.5)
        self.assertIn("no permite continuar", connector.status_message)

    @patch("jobs.connectors.computrabajo.socket.getaddrinfo")
    def test_external_redirect_is_rejected_before_following_destination(self, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        session = Mock()
        session.get.return_value = Mock(
            status_code=302, headers={"Location": "https://example.org/ofertas-de-trabajo/job"}, text="",
        )

        with self.assertRaises(ValueError):
            ComputrabajoConnector(session=session).fetch_details([
                ComputrabajoConnector().parse(
                    '<article class="box_offer" data-id="1"><a class="js-o-link" href="/ofertas-de-trabajo/job">Analista</a></article>',
                    "https://co.computrabajo.com/trabajo-de-analista",
                )[0],
            ])

        session.get.assert_called_once()

    def test_url_validator_rejects_untrusted_hosts_and_non_detail_paths(self):
        for url in (
            "http://co.computrabajo.com/ofertas-de-trabajo/job",
            "https://example.org/ofertas-de-trabajo/job",
            "https://co.computrabajo.com/trabajo-de-analista",
            "https://co.computrabajo.com@127.0.0.1/ofertas-de-trabajo/job",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_computrabajo_url(url, detail=True)

    @patch("jobs.connectors.computrabajo.socket.getaddrinfo")
    def test_private_dns_destination_is_rejected_before_request(self, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("127.0.0.1", 443))]
        session = Mock()
        listing = ComputrabajoConnector().parse(
            '<article class="box_offer" data-id="1"><a class="js-o-link" href="/ofertas-de-trabajo/job">Analista</a></article>',
            "https://co.computrabajo.com/trabajo-de-analista",
        )[0]

        connector = ComputrabajoConnector(session=session)
        results = connector.fetch_details([listing])

        self.assertEqual(results, [listing])
        self.assertIn("dirección pública", connector.status_message)
        session.get.assert_not_called()

    def test_connector_is_registered_and_equivalent_searches_are_grouped(self):
        connector = next(item for item in configured_connectors() if item.source == "computrabajo_co")
        requests = [
            {"profile_id": 1, "keywords": ["Analista"], "locations": ["Medellín"], "remote_ok": False,
             "matching_config_id": 7},
            {"profile_id": 2, "keywords": [" analista "], "locations": ["medellín"], "remote_ok": False,
             "matching_config_id": 7},
        ]

        groups = group_search_requests(connector, requests)

        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]["members"]), 2)
        self.assertEqual({item["profile_id"] for item in groups[0]["members"]}, {1, 2})

    @patch("jobs.tasks.finish_run")
    @patch("jobs.tasks.JobSourceStatus.objects.update_or_create")
    def test_partial_fetch_is_recorded_unavailable_with_counts(self, update_status, finish_run):
        connector = SimpleNamespace(source="computrabajo_co", status_message="Computrabajo bloqueó la ficha.")
        fetched = SourceFetchSummary(
            listings=[object()], listing_count=4, title_kept_count=2,
            title_discarded_count=2, details_requested_count=2,
            details_received_count=2, source_available=False,
        )
        saved = SimpleNamespace(
            vacancies=[object()], new_count=1, known_count=0,
            known_updated_count=0, known_unchanged_count=0,
        )
        run = object()
        checked_at = object()

        _record_source_fetch_outcome(connector, fetched, saved, run, checked_at)

        self.assertFalse(update_status.call_args.kwargs["defaults"]["available"])
        self.assertEqual(update_status.call_args.kwargs["defaults"]["last_vacancy_count"], 1)
        self.assertEqual(finish_run.call_args.kwargs["status"], OperationalRun.Status.PARTIAL)
        self.assertEqual(finish_run.call_args.kwargs["error_category"], "source_partially_unavailable")
        self.assertIn("bloqueó", finish_run.call_args.kwargs["error_summary"])

    @patch("matching.services.preselect_listing_titles")
    def test_shared_title_preselection_carries_partial_source_failure_without_losing_cards(self, preselect):
        from jobs.connectors.base import JobListing

        listing = JobListing("computrabajo_co", "1", "Analista", "Empresa", "Medellín", None,
                             "https://co.computrabajo.com/ofertas-de-trabajo/job")
        preselect.return_value = SimpleNamespace(listings=[listing], discarded_count=0, input_tokens=0)
        class PartialConnector:
            source = "computrabajo_co"

            def fetch_titles(self, *args, **kwargs):
                return [listing]

            def fetch_details(self, selected):
                raise SourcePartiallyUnavailable("bloqueo", selected)

        connector = PartialConnector()

        summary = _fetch_source_listings(connector, ["analista"], ["Medellín"], remote_ok=False)

        self.assertEqual(summary.listings, [listing])
        self.assertFalse(summary.source_available)
        self.assertEqual(summary.details_requested_count, 1)


