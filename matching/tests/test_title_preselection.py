from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from jobs.connectors.base import JobListing
from matching.services import preselect_listing_titles


def listing(title):
    return JobListing(
        source="elempleo_co",
        external_id="",
        title=title,
        company=None,
        location=None,
        description="Detalle que no debe participar en la clasificación",
        original_url=f"https://example.test/{title.casefold().replace(' ', '-')}",
    )


class TitlePreselectionTests(SimpleTestCase):
    @patch("matching.services.request_model_title_preselection")
    def test_discards_clear_mismatch_and_keeps_compatible_or_ambiguous_titles(self, request):
        titles = [
            listing("Auxiliar de cocina"),
            listing("Analista de procesos"),
            listing("Coordinador de operaciones"),
            listing("Jefe de área"),
        ]
        request.return_value = Mock(
            content={"decisions": [
                {"id": "0", "classification": "clearly_unrelated"},
                {"id": "1", "classification": "compatible"},
                {"id": "2", "classification": "uncertain"},
                {"id": "3", "classification": "clearly_unrelated"},
                {"id": "3", "classification": "clearly_unrelated"},
                {"id": "unknown", "classification": "clearly_unrelated"},
            ]},
            input_tokens=42,
        )

        result = preselect_listing_titles(titles, ["Analista de procesos"])

        self.assertEqual(
            [item.title for item in result.listings],
            ["Analista de procesos", "Coordinador de operaciones", "Jefe de área"],
        )
        self.assertEqual(result.discarded_count, 1)
        self.assertEqual(result.input_tokens, 42)
        request.assert_called_once()
        self.assertEqual(request.call_args.kwargs["search_terms"], ["Analista de procesos"])
        self.assertEqual(request.call_args.kwargs["vacancies"], [
            {"id": "0", "title": "Auxiliar de cocina"},
            {"id": "1", "title": "Analista de procesos"},
            {"id": "2", "title": "Coordinador de operaciones"},
            {"id": "3", "title": "Jefe de área"},
        ])

    @patch("matching.services.request_model_title_preselection")
    def test_keeps_every_title_when_call_fails_or_response_is_invalid(self, request):
        titles = [listing("Auxiliar de cocina"), listing("Analista de procesos")]
        request.side_effect = RuntimeError("private gateway payload")

        failed = preselect_listing_titles(titles, ["Analista de procesos"])
        self.assertEqual(failed.listings, titles)
        self.assertEqual(failed.discarded_count, 0)

        request.side_effect = None
        request.return_value = Mock(content={"decisions": [
            {"id": "0", "classification": "unknown"},
            {"id": "1", "keep": False},
        ]}, input_tokens=8)
        invalid = preselect_listing_titles(titles, ["Analista de procesos"])
        self.assertEqual(invalid.listings, titles)
        self.assertEqual(invalid.discarded_count, 0)
        self.assertEqual(invalid.input_tokens, 8)

    @patch("matching.services.request_model_title_preselection")
    def test_limits_batch_size_and_sums_reported_tokens(self, request):
        titles = [listing(f"Cargo {index}") for index in range(51)]
        request.side_effect = [
            Mock(content={"decisions": []}, input_tokens=12),
            Mock(content={"decisions": []}, input_tokens=7),
        ]

        result = preselect_listing_titles(titles, ["Cargo"])

        self.assertEqual(len(result.listings), 51)
        self.assertEqual(result.input_tokens, 19)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(len(request.call_args_list[0].kwargs["vacancies"]), 50)
        self.assertEqual(request.call_args_list[1].kwargs["vacancies"], [{"id": "50", "title": "Cargo 50"}])
