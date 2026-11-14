from django.conf import settings
from django.test import SimpleTestCase


from operations.schedules import DatabaseRefreshInterval


class RefreshScheduleTests(SimpleTestCase):
    def test_refresh_is_scheduled_at_configured_interval(self):
        schedule = settings.CELERY_BEAT_SCHEDULE["refresh-job-sources"]
        self.assertEqual(schedule["task"], "jobs.tasks.refresh_periodic_sources")
        self.assertIsInstance(schedule["schedule"], DatabaseRefreshInterval)
        self.assertEqual(schedule["schedule"].run_every.total_seconds(), settings.JOB_REFRESH_MINUTES * 60)
