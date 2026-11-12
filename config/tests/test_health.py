from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase, override_settings
from redis.exceptions import RedisError


class HealthEndpointTests(TestCase):
    @override_settings(SECURE_SSL_REDIRECT=True, SECURE_REDIRECT_EXEMPT=[r"^healthz$", r"^readyz$"])
    def test_http_health_probes_are_exempt_but_application_routes_redirect(self):
        with patch("config.health.Redis.from_url") as redis_from_url:
            redis_from_url.return_value.ping.return_value = True
            health = self.client.get("/healthz", secure=False)
            ready = self.client.get("/readyz", secure=False)
        ordinary = self.client.get("/accounts/login/", secure=False)

        self.assertEqual(health.status_code, 200)
        self.assertEqual(ready.status_code, 200)
        self.assertEqual(ordinary.status_code, 301)
        self.assertEqual(ordinary["Location"], "https://testserver/accounts/login/")

        with patch("config.health.Redis.from_url", side_effect=RedisError("private redis error")):
            unavailable = self.client.get("/readyz", secure=False)
        self.assertEqual(unavailable.status_code, 503)
        self.assertEqual(unavailable.json(), {"status": "unavailable"})
        self.assertNotIn("private redis error", unavailable.content.decode())

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

    @patch("config.health.connection.cursor", side_effect=DatabaseError("private database error"))
    @patch("config.health.Redis.from_url")
    def test_readyz_returns_generic_unavailable_when_database_fails(self, redis_from_url, _cursor):
        response = self.client.get("/readyz")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertNotIn("private database error", response.content.decode())
        redis_from_url.assert_not_called()

    @patch("config.health.Redis.from_url")
    def test_readyz_returns_generic_unavailable_when_redis_fails(self, redis_from_url):
        redis_from_url.return_value.ping.side_effect = RedisError("private redis error")

        response = self.client.get("/readyz")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertNotIn("private redis error", response.content.decode())
