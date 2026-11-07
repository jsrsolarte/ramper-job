from types import SimpleNamespace
from unittest import TestCase

from jobs.search_groups import group_search_requests, search_request_identity


class SearchGroupIdentityTests(TestCase):
    def setUp(self):
        self.connector = SimpleNamespace(source="elempleo_co")
        self.base = {
            "matching_config_id": 12,
            "keywords": ["Analista de procesos", "mejora continua"],
            "locations": ["Medellín", "Envigado"],
            "remote_ok": False,
        }

    def test_normalizes_case_spacing_and_order_for_equivalent_requests(self):
        equivalent = {
            **self.base,
            "keywords": [" MEJORA   CONTINUA ", "analista de procesos"],
            "locations": ["envigado", "  MEDELLÍN "],
        }

        self.assertEqual(
            search_request_identity(self.connector, self.base),
            search_request_identity(self.connector, equivalent),
        )
        groups = group_search_requests(self.connector, [self.base, equivalent])
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]["members"]), 2)

    def test_different_effective_criteria_remain_separate(self):
        requests = [
            self.base,
            {**self.base, "keywords": ["Ingeniero de procesos"]},
            {**self.base, "locations": ["Bogotá"]},
            {**self.base, "remote_ok": True},
            {**self.base, "matching_config_id": 13},
        ]

        self.assertEqual(len(group_search_requests(self.connector, requests)), len(requests))
