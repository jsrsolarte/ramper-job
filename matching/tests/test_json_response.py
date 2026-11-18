import json
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from requests import HTTPError, Timeout

from matching.client import OmniRouteError, request_model_analysis, request_model_organization
from matching.json_response import ModelJSONParseError, parse_model_json_object
from matching.schemas import InvalidAnalysisError, validate_analysis


class ModelJSONResponseTests(SimpleTestCase):
    def test_accepts_direct_object_and_one_complete_fenced_object(self):
        expected = {"message": "contenido sintético"}

        self.assertEqual(parse_model_json_object(json.dumps(expected)), expected)
        self.assertEqual(parse_model_json_object(f"```json\n{json.dumps(expected)}\n```"), expected)
        self.assertEqual(parse_model_json_object(f"```\n{json.dumps(expected)}\n```"), expected)

    def test_rejects_text_around_fence_multiple_fences_and_incomplete_fence(self):
        values = (
            'Resultado:\n```json\n{"ok": true}\n```',
            '```json\n{"ok": true}\n```\n```json\n{"ok": false}\n```',
            '```json\n{"ok": true}',
        )
        for value in values:
            with self.subTest(value=value), self.assertRaises(ModelJSONParseError) as caught:
                parse_model_json_object(value)
            self.assertFalse(caught.exception.repair_allowed)
            self.assertIsNone(caught.exception.repair_candidate)

    def test_only_syntactically_invalid_unambiguous_content_is_repairable(self):
        for value in ('{"ok":', '```json\n{"ok":\n```'):
            with self.subTest(value=value), self.assertRaises(ModelJSONParseError) as caught:
                parse_model_json_object(value)
            self.assertTrue(caught.exception.repair_allowed)
            self.assertIsNotNone(caught.exception.repair_candidate)

    def test_valid_non_object_json_and_oversized_json_are_not_repairable(self):
        for value, limit in (("[1, 2]", 100), ('{"ok": true}', 4)):
            with self.subTest(value=value), self.assertRaises(ModelJSONParseError) as caught:
                parse_model_json_object(value, max_chars=limit)
            self.assertFalse(caught.exception.repair_allowed)

    @override_settings(
        OMNIROUTE_BASE_URL="http://omniroute.internal/v1",
        OMNIROUTE_API_KEY="",
        OMNIROUTE_MODEL="auto",
        OMNIROUTE_TIMEOUT_SECONDS=5,
    )
    @patch("matching.client.requests.post")
    def test_valid_json_with_invalid_rubric_is_rejected_without_repair(self, post):
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": '{"rubric_version": 3}'}}]}
        post.return_value = response

        result = request_model_analysis(
            profile_text="CV sintético", search_phrases=[], locations=[], remote_ok=False,
            vacancy={}, prompt="Evalúa", parameters={}, rubric_version=3,
        )

        with self.assertRaises(InvalidAnalysisError):
            validate_analysis(result.content, rubric_version=3)
        post.assert_called_once()

    @override_settings(
        OMNIROUTE_BASE_URL="http://omniroute.internal/v1",
        OMNIROUTE_API_KEY="",
        OMNIROUTE_MODEL="auto",
        OMNIROUTE_TIMEOUT_SECONDS=5,
    )
    @patch("matching.client.requests.post")
    def test_valid_fenced_score_json_for_current_rubric_uses_one_call(self, post):
        response = Mock()
        response.json.return_value = {
            "choices": [{"message": {"content": '```json\n{"rubric_version": 3}\n```'}}]
        }
        post.return_value = response

        result = request_model_analysis(
            profile_text="CV sintético",
            search_phrases=["Analista"],
            locations=["Bogotá"],
            remote_ok=False,
            vacancy={"title": "Vacante sintética"},
            prompt="Evalúa datos sintéticos",
            parameters={},
            rubric_version=3,
        )

        self.assertEqual(result.content, {"rubric_version": 3})
        post.assert_called_once()

    @patch("matching.client.requests.post")
    def test_legacy_rubric_is_rejected_before_a_model_call(self, post):
        with self.assertRaises(ValueError):
            request_model_analysis(
                profile_text="CV sintético", search_phrases=[], locations=[], remote_ok=False,
                vacancy={}, prompt="Evalúa", parameters={}, rubric_version=2,
            )
        post.assert_not_called()

    @override_settings(
        OMNIROUTE_BASE_URL="http://omniroute.internal/v1",
        OMNIROUTE_API_KEY="",
        OMNIROUTE_MODEL="auto",
        OMNIROUTE_TIMEOUT_SECONDS=5,
    )
    @patch("matching.client.requests.post")
    def test_score_requests_include_a_versioned_strict_schema(self, post):
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": '{"ok": true}'}}]}
        post.return_value = response

        request_model_analysis(
            profile_text="CV sintético", search_phrases=[], locations=[], remote_ok=False,
            vacancy={}, prompt="Evalúa", parameters={}, rubric_version=3,
        )
        structured = post.call_args.kwargs["json"]["response_format"]
        self.assertEqual(structured["type"], "json_schema")
        schema = structured["json_schema"]
        self.assertEqual(schema["name"], "vacancy_score_v3")
        self.assertTrue(schema["strict"])
        self.assertEqual(schema["schema"]["properties"]["score_breakdown"]["properties"]["skills"]["properties"]["score"]["multipleOf"], 0.05)

    @override_settings(
        OMNIROUTE_BASE_URL="http://omniroute.internal/v1",
        OMNIROUTE_API_KEY="",
        OMNIROUTE_MODEL="auto",
        OMNIROUTE_TIMEOUT_SECONDS=5,
    )
    @patch("matching.client.requests.post")
    def test_organization_requests_include_its_versioned_schema(self, post):
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": '{"summary": "Resumen"}'}}]}
        post.return_value = response

        request_model_organization(vacancy={}, prompt="Organiza", parameters={})

        schema = post.call_args.kwargs["json"]["response_format"]["json_schema"]
        self.assertEqual(schema["name"], "vacancy_organization_v1")
        self.assertTrue(schema["strict"])
        self.assertEqual(schema["schema"]["required"], ["summary", "keywords", "responsibilities", "requirements", "conditions"])

    @override_settings(
        OMNIROUTE_BASE_URL="http://omniroute.internal/v1",
        OMNIROUTE_API_KEY="",
        OMNIROUTE_MODEL="auto",
        OMNIROUTE_TIMEOUT_SECONDS=5,
    )
    @patch("matching.client.requests.post")
    def test_explicit_structured_output_rejection_falls_back_once(self, post):
        rejected = Mock()
        rejected.status_code = 400
        rejected.json.return_value = {"error": {"code": "unsupported_response_format"}}
        rejected.raise_for_status.side_effect = HTTPError(response=rejected)
        success = Mock()
        success.json.return_value = {"choices": [{"message": {"content": '{"summary": "Resumen"}'}}]}
        post.side_effect = [rejected, success]

        result = request_model_organization(vacancy={"title": "Vacante sintética"}, prompt="Organiza", parameters={})

        self.assertEqual(result.content, {"summary": "Resumen"})
        self.assertEqual(post.call_count, 2)
        self.assertIn("response_format", post.call_args_list[0].kwargs["json"])
        self.assertNotIn("response_format", post.call_args_list[1].kwargs["json"])

    @override_settings(
        OMNIROUTE_BASE_URL="http://omniroute.internal/v1",
        OMNIROUTE_API_KEY="",
        OMNIROUTE_MODEL="auto",
        OMNIROUTE_TIMEOUT_SECONDS=5,
    )
    @patch("matching.client.requests.post")
    def test_timeout_and_authentication_errors_do_not_fall_back(self, post):
        post.side_effect = Timeout()
        with self.assertRaises(OmniRouteError) as timeout:
            request_model_organization(vacancy={}, prompt="Organiza", parameters={})
        self.assertEqual(timeout.exception.category, "omniroute.timeout")
        post.assert_called_once()

        post.reset_mock()
        post.side_effect = None
        rejected = Mock()
        rejected.status_code = 401
        rejected.json.return_value = {"error": {"code": "unauthorized"}}
        rejected.raise_for_status.side_effect = HTTPError(response=rejected)
        post.return_value = rejected
        with self.assertRaises(OmniRouteError) as auth:
            request_model_organization(vacancy={}, prompt="Organiza", parameters={})
        self.assertEqual(auth.exception.category, "omniroute.http_401")
        post.assert_called_once()

    @override_settings(
        OMNIROUTE_BASE_URL="http://omniroute.internal/v1",
        OMNIROUTE_API_KEY="",
        OMNIROUTE_MODEL="auto",
        OMNIROUTE_TIMEOUT_SECONDS=5,
    )
    @patch("matching.client.requests.post")
    def test_syntax_repair_uses_one_context_free_call_and_preserves_values(self, post):
        malformed = Mock()
        malformed.json.return_value = {
            "choices": [{"message": {"content": '{"summary": "Resumen sintético" "keywords": ["SQL"], "responsibilities": [], "requirements": [], "conditions": []}'}}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 10},
        }
        repaired = Mock()
        repaired.json.return_value = {
            "choices": [{"message": {"content": '{"summary": "Resumen sintético", "keywords": ["SQL"], "responsibilities": [], "requirements": [], "conditions": []}'}}],
            "usage": {"prompt_tokens": 30, "completion_tokens": 12},
        }
        post.side_effect = [malformed, repaired]

        result = request_model_organization(
            vacancy={"description": "vacante que no debe entrar a reparación"},
            prompt="prompt original que no debe entrar a reparación",
            parameters={},
        )

        self.assertEqual(result.content["summary"], "Resumen sintético")
        self.assertEqual(result.content["keywords"], ["SQL"])
        self.assertEqual(result.format_action, "repair_succeeded")
        self.assertEqual(result.repair_input_tokens, 30)
        self.assertEqual(result.repair_output_tokens, 12)
        self.assertEqual(post.call_count, 2)
        repair_payload = post.call_args_list[1].kwargs["json"]
        repair_user_data = json.loads(repair_payload["messages"][1]["content"])
        self.assertEqual(set(repair_user_data), {"malformed_content", "required_schema"})
        self.assertNotIn("vacante que no debe entrar", repair_payload["messages"][1]["content"])
        self.assertNotIn("prompt original", repair_payload["messages"][0]["content"])

    @override_settings(
        OMNIROUTE_BASE_URL="http://omniroute.internal/v1",
        OMNIROUTE_API_KEY="",
        OMNIROUTE_MODEL="auto",
        OMNIROUTE_TIMEOUT_SECONDS=5,
    )
    @patch("matching.client.requests.post")
    def test_repair_rejects_changed_values_and_ambiguous_content_is_never_repaired(self, post):
        malformed = Mock()
        malformed.json.return_value = {"choices": [{"message": {"content": '{"summary": "Original" "keywords": []}'}}]}
        altered = Mock()
        altered.json.return_value = {"choices": [{"message": {"content": '{"summary": "Inventado", "keywords": []}'}}]}
        post.side_effect = [malformed, altered]
        with self.assertLogs("matching.client", level="WARNING") as captured:
            with self.assertRaises(OmniRouteError) as changed:
                request_model_organization(vacancy={}, prompt="Organiza", parameters={})
        self.assertEqual(changed.exception.category, "omniroute.repair_not_preserved")
        self.assertNotIn("Original", str(changed.exception))
        self.assertNotIn("Inventado", str(changed.exception))
        self.assertNotIn("Original", " ".join(captured.output))
        self.assertNotIn("Inventado", " ".join(captured.output))
        self.assertEqual(post.call_count, 2)

        post.reset_mock()
        post.side_effect = None
        ambiguous = Mock()
        ambiguous.json.return_value = {
            "choices": [{"message": {"content": '```json\n{"summary": "Uno"}\n```\n```json\n{"summary": "Dos"}\n```'}}]
        }
        post.return_value = ambiguous
        with self.assertRaises(OmniRouteError) as rejected:
            request_model_organization(vacancy={}, prompt="Organiza", parameters={})
        self.assertEqual(rejected.exception.category, "omniroute.ambiguous_content")
        post.assert_called_once()

