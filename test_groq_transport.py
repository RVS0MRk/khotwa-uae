"""Exercise real request construction with mocked HTTP; never calls Groq."""
import contextlib
import io
import json
import os
import unittest
from unittest.mock import Mock, patch

os.environ["GROQ_API_KEY"] = "test-only-placeholder"
import app as startsmart
import test_api
from test_browser_server import DIRTY_ADVISOR


def response(content, finish="stop", status=200):
    reply = Mock(status_code=status)
    reply.json.return_value = {"choices": [{"finish_reason": finish, "message": {
        "content": content, "reasoning": "PRIVATE REASONING MUST NEVER APPEAR"}}],
        "usage": {"completion_tokens": 20, "completion_tokens_details": {"reasoning_tokens": 18}}}
    return reply


class GroqTransportTests(unittest.TestCase):
    def setUp(self):
        self.client = startsmart.app.test_client()

    def test_empty_length_completion_fails_before_parsing_on_all_routes(self):
        for endpoint, payload, status in (("/generate", {"idea": "Tutoring"}, 500),
                                         ("/ask", {"question": "How can I test?"}, 503),
                                         ("/discover", {"skills": "Teaching"}, 503)):
            with self.subTest(endpoint=endpoint), patch("groq_client.requests.post", return_value=response("", "length")), \
                 patch.object(startsmart, "_parse_advisor") as parse_advisor, \
                 patch.object(startsmart, "_normalize_plan") as normalize, \
                 self.assertLogs(startsmart.app.logger, level="ERROR") as logs:
                result = self.client.post(endpoint, json=payload)
            self.assertEqual(result.status_code, status)
            parse_advisor.assert_not_called()
            normalize.assert_not_called()
            log = " ".join(logs.output)
            for expected in (endpoint, '"http_status": 200', '"finish_reason": "length"', '"content_empty": true',
                             '"reasoning_tokens": 18', "empty final message.content", "GroqGenerationError"):
                self.assertIn(expected, log)
            for forbidden in ("PRIVATE REASONING", "test-only-placeholder", "Authorization", "JSONDecodeError"):
                self.assertNotIn(forbidden, log)
                self.assertNotIn(forbidden, result.get_data(as_text=True))

    def test_valid_content_and_route_specific_settings(self):
        idea = {"name": "Tutoring", "fit": "Teaching skill", "customer": "Students",
                "first_test": "Interview students", "assumption": "Learning support is needed", "category": "Education & Tutoring"}
        cases = [("/generate", {"idea": "Tutoring"}, {"opportunity_score": {"total": 15}}, 5000),
                 ("/ask", {"question": "How can I test?"}, DIRTY_ADVISOR, 1200),
                 ("/discover", {"skills": "Teaching"}, {"ideas": [idea] * 3}, 2500)]
        for endpoint, payload, content, tokens in cases:
            with self.subTest(endpoint=endpoint), patch("groq_client.requests.post", return_value=response(json.dumps(content))) as post:
                result = self.client.post(endpoint, json=payload)
            self.assertEqual(result.status_code, 200)
            body = post.call_args.kwargs["json"]
            self.assertEqual(body["model"], "openai/gpt-oss-120b")
            self.assertEqual(body["max_completion_tokens"], tokens)
            self.assertNotIn("max_tokens", body)
            self.assertEqual(body["reasoning_effort"], "low")
            self.assertIs(body["include_reasoning"], False)
            self.assertEqual(body["response_format"], {"type": "json_object"})
            self.assertNotIn("PRIVATE REASONING", result.get_data(as_text=True))
            if endpoint == "/generate":
                self.assertEqual(result.get_json()["state"]["idea"], "Tutoring")
            elif endpoint == "/ask":
                answer = result.get_json()["answer"]
                self.assertEqual(answer["title"], "Test customer demand first")
                self.assertEqual(answer["points"][0]["text"], "Interview five potential customers.")
            else:
                self.assertEqual(len(result.get_json()["ideas"]), 3)

    def test_http_error_diagnostics_redact_secrets(self):
        reply = response("", status=401)
        reply.json.return_value = {"error": {"message": "Invalid API key: test-only-placeholder; Bearer gsk_dummy; retry later"}}
        with patch("groq_client.requests.post", return_value=reply), self.assertLogs(startsmart.app.logger, level="ERROR") as logs:
            result = self.client.post("/generate", json={"idea": "Tutoring"})
        log = " ".join(logs.output)
        self.assertEqual(result.status_code, 500)
        for text in ('"http_status": 401', '"exception_type": "HTTPError"', "retry later", "[REDACTED]"):
            self.assertIn(text, log)
        for text in ("test-only-placeholder", "gsk_dummy", "Bearer"):
            self.assertNotIn(text, log)

    def test_invalid_final_json_keeps_http_metadata(self):
        with patch("groq_client.requests.post", return_value=response("not JSON")), self.assertLogs(startsmart.app.logger, level="ERROR") as logs:
            result = self.client.post("/generate", json={"idea": "Tutoring"})
        self.assertEqual(result.status_code, 500)
        log = " ".join(logs.output)
        for text in ('"http_status": 200', '"finish_reason": "stop"', '"content_empty": false', "JSONDecodeError", "Invalid JSON in final message.content"):
            self.assertIn(text, log)

    def test_smoke_test_requires_exact_final_answer_and_correct_settings(self):
        output = io.StringIO()
        with patch("groq_client.requests.post", return_value=response(" Groq connection works \n")) as post, contextlib.redirect_stdout(output):
            test_api.main()
        body = post.call_args.kwargs["json"]
        self.assertEqual(body["max_completion_tokens"], 200)
        self.assertEqual(body["reasoning_effort"], "low")
        self.assertIs(body["include_reasoning"], False)
        self.assertNotIn("response_format", body)
        self.assertIn("PASS: Groq connection works", output.getvalue())
        self.assertNotIn("PRIVATE REASONING", output.getvalue())
        for content, finish in (("", "length"), ("Something else", "stop")):
            with patch("groq_client.requests.post", return_value=response(content, finish)), \
                 self.assertLogs("test_api", level="ERROR"), self.assertRaisesRegex(SystemExit, "FAIL:"):
                test_api.main()

    def test_timeout_and_truncated_content_have_clear_diagnostics(self):
        import requests
        for reply, error, expected in ((None, requests.Timeout("secret request details"), "Timeout"),
                                       (response('{"partial":', "length"), None, "token limit")):
            with patch("groq_client.requests.post", return_value=reply, side_effect=error), \
                 self.assertLogs(startsmart.app.logger, level="ERROR") as logs:
                result = self.client.post("/generate", json={"idea": "Tutoring"})
            self.assertEqual(result.status_code, 500)
            self.assertIn(expected, " ".join(logs.output))
            self.assertNotIn("secret request details", " ".join(logs.output))
