import json
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from matching.client import (
    OmniRouteError,
    request_model_analysis,
    request_model_keywords,
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
            profile_text="Experiencia con datos",
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

    @override_settings(OMNIROUTE_BASE_URL="", OMNIROUTE_MODEL="")
    def test_missing_endpoint_or_model_is_reported(self):
        with self.assertRaises(OmniRouteError):
            request_model_analysis(
                profile_text="", search_phrases=[], locations=[], remote_ok=False,
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
                profile_text="private CV", search_phrases=[], locations=[], remote_ok=False,
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
            profile_text="Experiencia en mejora de procesos",
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
            "choices": [{"message": {"content": '{"decisions": [{"id": "0", "keep": false}]}'}}],
            "usage": {"prompt_tokens": 31},
        }
        post.return_value = response

        result = request_model_title_preselection(
            search_terms=["Analista de procesos"],
            vacancies=[{"id": "0", "title": "Auxiliar de cocina"}],
        )

        self.assertEqual(result.content, {"decisions": [{"id": "0", "keep": False}]})
        self.assertEqual(result.input_tokens, 31)
        payload = post.call_args.kwargs["json"]
        body = payload["messages"][1]["content"]
        self.assertIn('"search_terms": ["Analista de procesos"]', body)
        self.assertIn('"title": "Auxiliar de cocina"', body)
        self.assertNotIn("cv", body.casefold())
        self.assertNotIn("description", body.casefold())
