import io
import os
import unittest
from unittest.mock import patch
from pypdf import PdfReader

from test_support import configure_mock_environment
configure_mock_environment()
import app as khotwa
from test_finance import BASE


class V2BackendTests(unittest.TestCase):
    def setUp(self):
        self.client = khotwa.app.test_client()

    def test_finance_endpoint_does_not_use_groq(self):
        with patch.object(khotwa, "call_groq") as provider:
            response = self.client.post("/finance", json={"inputs": BASE})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["base"]["operating_profit"], "1800.00")
        provider.assert_not_called()

    def test_finance_route_invalid_and_missing(self):
        self.assertEqual(self.client.post("/finance", json={"inputs": {"price": -1}}).status_code, 400)
        response = self.client.post("/finance", json={"inputs": {}})
        self.assertIsNone(response.get_json()["base"]["startup_capital"])
        self.assertEqual(self.client.post("/finance", json={"inputs": BASE, "scenarios": []}).status_code, 400)

    def test_investment_pdf_recalculates_tampered_results(self):
        payload = {"finance": {"inputs": BASE, "result": {"operating_profit": "99999999"}},
                   "plan": {"state": {"idea": "Small booking service"}}, "notes": {"model": "Per booking"}}
        for language in ("en", "ar"):
            response = self.client.post("/investment/pdf", json={**payload, "lang": language})
            self.assertEqual(response.status_code, 200)
            reader = PdfReader(io.BytesIO(response.data))
            text = "\n".join(p.extract_text() for p in reader.pages)
            self.assertIn("1,800.00 AED", text)
            self.assertNotIn("99999999", text)
            self.assertGreaterEqual(len(reader.pages), 2)

    def test_security_headers_and_no_inline_scripts(self):
        response = self.client.get("/")
        self.assertIn("script-src 'self'", response.headers["Content-Security-Policy"])
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        html = response.get_data(as_text=True)
        self.assertNotRegex(html, r"<[^>]+\sonclick=")
        self.assertNotIn("<script>", html)
        self.assertNotIn("cdn.jsdelivr.net", html)

    def test_financial_context_recomputed_and_customer_notes_excluded(self):
        context = khotwa._short_context({"_financial_inputs": BASE, "proof_summary": {
            "total_responses": 1, "top_concern": "Private customer detail", "actual_payments": 0}})
        self.assertIn("1800.00", context)
        self.assertNotIn("Private customer detail", context)

    def test_pdf_limits_and_busy(self):
        self.assertEqual(self.client.post("/investment/pdf", json={"notes": {"model": "x"*1001}}).status_code, 400)
        khotwa._pdf_lock.acquire()
        try:
            self.assertEqual(self.client.post("/investment/pdf", json={"finance": {"inputs": BASE}}).status_code, 503)
        finally:
            khotwa._pdf_lock.release()

    def test_founder_report_keeps_finance_when_using_language_variant(self):
        plan = {"_content_lang": "en", "_financial_inputs": BASE, "state": {"idea": "Booking tool"},
                "_alternate_plan": {"_content_lang": "ar", "state": {"idea": "Booking tool"}}}
        localized = khotwa._localize_pdf_plan(plan, "ar")
        self.assertEqual(localized["_financial_inputs"], BASE)

    def test_model_target_cannot_contaminate_business_segment_fallback(self):
        names = khotwa._segment_names("Digital booking tool", "Residential car owners", "Technology & Digital", "en")
        self.assertIn("Small business operators", names)
        self.assertFalse(any("car" in name.lower() for name in names))
