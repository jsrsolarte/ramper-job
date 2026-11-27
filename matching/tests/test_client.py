import json
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from matching.client import (
    OmniRouteError,
    request_model_analysis,
    request_model_keywords,
    request_model_profile_artifacts,
    request_model_title_preselection,
)


class OmniRouteClientTests(SimpleTestCase):
    @override_settings(
        OMNIROUTE_BASE_URL="http://omniroute.internal/v1",
        OMNIROUTE_API_KEY="test-secret",
        OMNIROUTE_MODEL="private-model",
        OMNIROUTE_TIMEOUT_SECONDS=9,
    )
    @patch("matching.client.requests.post")
    def test_calls_configured_model_using_chat_completions_contract(self, post):
        result = {"organized_description": "Descripción organizada", "score": 81, "reasons": ["Experiencia"], "gaps": []}
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": json.dumps(result)}}]}
        post.return_value = response

        actual = request_model_analysis(
            profile_evidence=[{"id": "f1", "category": "skill", "statement": "SQL", "source_excerpt": "SQL"}],
            search_phrases=["Analista en Cali"],
            locations=["Cali"],
            remote_ok=False,
            vacancy={"title": "Analista"},
            prompt="Evalúa objetivamente",
            parameters={"temperature": 0.2},
        )

        self.assertEqual(actual.content, result)
        self.assertIsNone(actual.input_tokens)
        self.assertIsNone(actual.output_tokens)
        args, kwargs = post.call_args
        self.assertEqual(args[0], "http://omniroute.internal/v1/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-secret")
        self.assertEqual(kwargs["timeout"], 9)
        self.assertEqual(kwargs["json"]["model"], "private-model")
        self.assertEqual(kwargs["json"]["temperature"], 0.2)
        body = json.loads(kwargs["json"]["messages"][1]["content"])
        self.assertIn("profile_evidence", body)
        self.assertNotIn("cv", body)

    @override_settings(OMNIROUTE_BASE_URL="", OMNIROUTE_MODEL="")
    def test_missing_endpoint_or_model_is_reported(self):
        with self.assertRaises(OmniRouteError):
            request_model_analysis(
                profile_evidence=[], search_phrases=[], locations=[], remote_ok=False,
                vacancy={}, prompt="", parameters={}
            )

    @override_settings(
        OMNIROUTE_BASE_URL="http://omniroute.internal/v1",
        OMNIROUTE_API_KEY="test-secret",
        OMNIROUTE_MODEL="auto",
        OMNIROUTE_TIMEOUT_SECONDS=9,
    )
    @patch("matching.client.requests.post")
    def test_unsupported_auto_candidates_are_classified_without_storing_gateway_message(self, post):
        from requests import HTTPError

        response = Mock()
        response.status_code = 400
        response.json.return_value = {
            "error": {"message": "requested model is not supported; private payload follows"}
        }
        response.raise_for_status.side_effect = HTTPError(response=response)
        post.return_value = response

        with self.assertRaises(OmniRouteError) as caught:
            request_model_keywords(
                profile_evidence=[{"statement": "SQL", "source_excerpt": "SQL"}], search_phrases=[], locations=[], remote_ok=False,
                prompt="private prompt", parameters={},
            )

        self.assertEqual(caught.exception.category, "omniroute.model_unsupported")
        self.assertEqual(str(caught.exception), "La combinación de OmniRoute seleccionó modelos no compatibles.")
        self.assertNotIn("private", str(caught.exception))

    @override_settings(
        OMNIROUTE_BASE_URL="http://omniroute.internal/v1",
        OMNIROUTE_API_KEY="",
        OMNIROUTE_MODEL="private-model",
        OMNIROUTE_TIMEOUT_SECONDS=9,
    )
    @patch("matching.client.requests.post")
    def test_requests_profile_search_keywords_as_structured_json(self, post):
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": '{"keywords": ["procesos"]}'}}]}
        post.return_value = response

        result = request_model_keywords(
            profile_evidence=[{"statement": "Mejora de procesos", "source_excerpt": "Mejoré procesos"}],
            search_phrases=["Analista de procesos en Bogotá"],
            locations=["Bogotá"],
            remote_ok=False,
            prompt="Propón términos de cargo",
            parameters={"temperature": 0.1},
        )

        self.assertEqual(result.content, {"keywords": ["procesos"]})
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["messages"][0]["content"], "Propón términos de cargo")
        self.assertIn('"search_phrases": ["Analista de procesos en Bogotá"]', payload["messages"][1]["content"])
        self.assertIn('"keywords": ["string"]', payload["messages"][1]["content"])
        self.assertIn('"profile_evidence"', payload["messages"][1]["content"])
        self.assertNotIn('"cv"', payload["messages"][1]["content"])

    @override_settings(
        OMNIROUTE_BASE_URL="http://omniroute.internal/v1",
        OMNIROUTE_API_KEY="",
        OMNIROUTE_MODEL="private-model",
        OMNIROUTE_TIMEOUT_SECONDS=9,
    )
    @patch("matching.client.requests.post")
    def test_profile_artifact_request_returns_evidence_and_keywords_together(self, post):
        response = Mock()
        response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({"facts": [], "keywords": ["Analista"]})}}],
            "usage": {"prompt_tokens": 250, "completion_tokens": 40},
        }
        post.return_value = response

        result = request_model_profile_artifacts(
            profile_text="CV sintético con experiencia en SQL",
            search_phrases=["Analista de datos"],
            locations=["Medellín"],
            remote_ok=False,
            prompt="Extrae evidencia y términos",
            parameters={"temperature": 0.1},
        )

        self.assertEqual(result.content, {"facts": [], "keywords": ["Analista"]})
        self.assertEqual(result.input_tokens, 250)
        body = json.loads(post.call_args.kwargs["json"]["messages"][1]["content"])
        self.assertEqual(body["cv"], "CV sintético con experiencia en SQL")
        self.assertIn('"source_excerpt"', post.call_args.kwargs["json"]["messages"][1]["content"])

    @override_settings(
        OMNIROUTE_BASE_URL="http://omniroute.internal/v1",
        OMNIROUTE_API_KEY="",
        OMNIROUTE_MODEL="private-model",
        OMNIROUTE_TIMEOUT_SECONDS=9,
    )
    @patch("matching.client.requests.post")
    def test_title_preselection_sends_only_titles_and_shared_search_terms(self, post):
        response = Mock()
        response.json.return_value = {
            "choices": [{"message": {"content": (
                '{"decisions": [{"id": "0", "classification": "clearly_unrelated"}]}'
            )}}],
            "usage": {"prompt_tokens": 31},
        }
        post.return_value = response

        result = request_model_title_preselection(
            search_terms=["Analista de procesos"],
            vacancies=[{"id": "0", "title": "Auxiliar de cocina"}],
        )

        self.assertEqual(result.content, {
            "decisions": [{"id": "0", "classification": "clearly_unrelated"}],
        })
        self.assertEqual(result.input_tokens, 31)
        payload = post.call_args.kwargs["json"]
        body = payload["messages"][1]["content"]
        prompt = payload["messages"][0]["content"]
        self.assertIn('"search_terms": ["Analista de procesos"]', body)
        self.assertIn('"title": "Auxiliar de cocina"', body)
        self.assertIn("Conserva cualquier título compatible, ambiguo o insuficiente", prompt)
        self.assertIn("classification=clearly_unrelated solo para incompatibilidades laborales obvias", prompt)
        self.assertIn('"classification": "compatible | uncertain | clearly_unrelated"', body)
        self.assertNotIn("cv", body.casefold())
        self.assertNotIn("description", body.casefold())
