from datetime import datetime, timedelta, timezone

from django.test import SimpleTestCase

from dashboard.time_format import publication_age, relative_age


class RelativeAgeTests(SimpleTestCase):
    def test_formats_minutes_hours_and_days_in_spanish(self):
        now = datetime(2026, 10, 30, 12, tzinfo=timezone.utc)

        self.assertEqual(relative_age(now - timedelta(minutes=30), now=now), "hace 30 min")
        self.assertEqual(relative_age(now - timedelta(hours=2), now=now), "hace 2 horas")
        self.assertEqual(relative_age(now - timedelta(days=1), now=now), "hace 1 día")

    def test_handles_missing_and_future_dates(self):
        now = datetime(2026, 10, 30, 12, tzinfo=timezone.utc)

        self.assertEqual(relative_age(None, now=now), "")
        self.assertEqual(relative_age(now + timedelta(minutes=5), now=now), "hace menos de un minuto")

    def test_handles_naive_values_using_the_current_timezone(self):
        now = datetime(2026, 10, 30, 12)

        self.assertEqual(relative_age(now - timedelta(hours=1), now=now), "hace 1 hora")

    def test_date_only_publication_uses_calendar_days_without_inventing_time(self):
        now = datetime(2026, 10, 30, 20, tzinfo=timezone.utc)

        age, absolute = publication_age(
            now.replace(hour=0), {"details": {"date_posted": "2026-10-30"}}, now=now
        )

        self.assertEqual(age, "hoy")
        self.assertEqual(absolute, "30/10/2026")
