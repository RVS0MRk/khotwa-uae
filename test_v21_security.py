"""Headers and explicit per-worker limiter semantics, without a network call."""

import os
import unittest
from unittest.mock import patch
from test_support import configure_mock_environment

configure_mock_environment()
import app as application


class RoundTwoSecurityTests(unittest.TestCase):
    def test_render_hsts_and_tighter_style_policy(self):
        with patch.dict(os.environ, {"RENDER": "true"}):
            headers = application.app.test_client().get("/health").headers
        self.assertEqual(headers["Strict-Transport-Security"], "max-age=31536000")
        self.assertIn("style-src-elem 'self'", headers["Content-Security-Policy"])
        self.assertNotIn("style-src 'self' 'unsafe-inline'", headers["Content-Security-Policy"])

    def test_each_worker_has_a_separate_limit_window(self):
        # Two independent stores model two Python worker processes. This proves
        # why the supported deployment uses one worker, not a shared global cap.
        workers = [{}, {}]
        with patch.dict(os.environ, {"RENDER": "true"}):
            for store in workers:
                with patch.object(application, "_request_times", store):
                    client = application.app.test_client()
                    for _ in range(30):
                        self.assertNotEqual(client.post("/ask", json={}).status_code, 429)
                    response = client.post("/ask", json={})
                    self.assertEqual(response.status_code, 429)
                    self.assertEqual(response.headers["Retry-After"], "600")
        self.assertIsNot(workers[0], workers[1])
