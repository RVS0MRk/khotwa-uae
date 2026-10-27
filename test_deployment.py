"""Offline checks for public request boundaries and bundled assets."""

import os
import unittest
from unittest.mock import patch

os.environ["GROQ_API_KEY"] = "test-only-placeholder"

import app as startsmart


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.client = startsmart.app.test_client()

    def test_health_and_static_assets(self):
        self.assertEqual(self.client.get("/health").get_json(), {"status": "ok"})
        for path in ("/static/startsmart.css", "/static/startsmart.js", "/static/favicon.svg"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                response.close()
        self.assertTrue(os.path.isfile(startsmart.AMIRI_PATH))

    def test_api_request_validation(self):
        self.assertEqual(self.client.post("/generate", data="hello").status_code, 415)
        self.assertEqual(self.client.post("/ask", data="[1]", content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/ask", json={"question": "x" * 501}).status_code, 400)
        self.assertEqual(self.client.post("/discover", json={"skills": "x" * 301}).status_code, 400)
        self.assertEqual(self.client.post("/pdf", json={"steps": [{}] * 31}).status_code, 400)
        self.assertEqual(self.client.post("/generate", data=" " * (256 * 1024 + 1),
                                          content_type="application/json").status_code, 413)

    def test_public_limit_applies_to_costly_routes_only(self):
        with patch.dict(os.environ, {"RENDER": "true"}):
            startsmart._request_times.clear()
            try:
                for _ in range(30):
                    response = self.client.post("/ask", json={"question": ""})
                    self.assertEqual(response.status_code, 200)
                limited = self.client.post("/ask", json={"question": ""})
                self.assertEqual(limited.status_code, 429)
                self.assertEqual(limited.get_json(), {"error": "rate_limited"})
                self.assertEqual(self.client.get("/health").status_code, 200)
            finally:
                startsmart._request_times.clear()

    def test_simultaneous_pdf_request_returns_json_busy(self):
        startsmart._pdf_lock.acquire()
        try:
            response = self.client.post("/pdf", json={"_lang": "en"})
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.get_json(), {"error": "pdf_busy"})
        finally:
            startsmart._pdf_lock.release()


if __name__ == "__main__":
    unittest.main()
