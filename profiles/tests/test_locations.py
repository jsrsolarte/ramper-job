from django.test import SimpleTestCase
from types import SimpleNamespace

from profiles.locations import BOGOTA_AREA, MEDELLIN_AREA, expand_locations, vacancy_location_is_eligible


class LocationExpansionTests(SimpleTestCase):
    def test_medellin_aliases_expand_to_the_valle_de_aburra(self):
        self.assertEqual(expand_locations(["Valle de Aburrá"]), list(MEDELLIN_AREA))
        self.assertEqual(expand_locations(["MEDELLIN, Antioquia"]), list(MEDELLIN_AREA))

    def test_bogota_aliases_expand_to_nearby_municipalities(self):
        self.assertEqual(expand_locations(["Bogotá D.C."]), list(BOGOTA_AREA))
        self.assertIn("Soacha", expand_locations(["Bogota y alrededores"]))

    def test_unknown_locations_remain_literal_and_duplicates_are_removed(self):
        self.assertEqual(expand_locations(["Cali", "CALI", "  Cali "]), ["Cali"])

    def test_vacancy_location_is_checked_against_expanded_profile_area(self):
        profile = SimpleNamespace(locations=["Medellín"], remote_ok=False)
        vacancy = SimpleNamespace(location="Bogotá · Av. 68", raw_data={"details": {"city": "Bogotá"}})

        self.assertFalse(vacancy_location_is_eligible(vacancy, profile))
        vacancy.location = "Envigado"
        vacancy.raw_data = {"details": {"city": "Envigado"}}
        self.assertTrue(vacancy_location_is_eligible(vacancy, profile))

    def test_remote_requires_opt_in_and_unknown_location_is_not_assumed_compatible(self):
        profile = SimpleNamespace(locations=["Medellín"], remote_ok=False)
        vacancy = SimpleNamespace(location=None, raw_data={"details": {"modality": "remoto"}})

        self.assertFalse(vacancy_location_is_eligible(vacancy, profile))
        profile.remote_ok = True
        self.assertTrue(vacancy_location_is_eligible(vacancy, profile))
        vacancy.raw_data = {"details": {}}
        self.assertFalse(vacancy_location_is_eligible(vacancy, profile))
