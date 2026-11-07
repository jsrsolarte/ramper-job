from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase
from redis.exceptions import RedisError


class HealthEndpointTests(TestCase):
    def test_healthz_is_public_and_confirms_process_liveness(self):
        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_collected_static_assets_are_served(self):
        response = self.client.get("/static/app.css")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/css", response["Content-Type"])

    @patch("config.health.Redis.from_url")
    def test_readyz_checks_database_and_redis(self, redis_from_url):
        redis_from_url.return_value.ping.return_value = True

        response = self.client.get("/readyz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready"})
        redis_from_url.return_value.ping.assert_called_once_with()
        redis_from_url.return_value.close.assert_called_once_with()

    @patch("config.health.connection.cursor", side_effect=DatabaseError("unavailable"))
    @patch("config.health.Redis.from_url")
    def test_readyz_returns_generic_unavailable_when_database_fails(self, redis_from_url, _cursor):
        response = self.client.get("/readyz")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        redis_from_url.assert_not_called()

    @patch("config.health.Redis.from_url")
    def test_readyz_returns_generic_unavailable_when_redis_fails(self, redis_from_url):
        redis_from_url.return_value.ping.side_effect = RedisError("private redis error")

        response = self.client.get("/readyz")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertNotIn("private redis error", response.content.decode())
