"""Offline reproductions of the live report; no provider or font downloads."""
import io
import json
import os
import unittest
from copy import deepcopy
from unittest.mock import Mock, patch

os.environ["GROQ_API_KEY"] = "test-only-placeholder"
import app as startsmart
from test_browser_server import DIRTY_ADVISOR, fake_groq
from pypdf import PdfReader


def example_plan():
    inputs = {"idea": "Mobile Car‑Interior Ergonomic Consulting", "category": "Services & Maintenance",
              "budget": 4000, "region": "Abu Dhabi", "context": "Local service"}
    return startsmart._normalize_plan(json.loads(fake_groq("plan", inputs["idea"])), inputs, "en")


class LiveRegressions(unittest.TestCase):
    def test_dirty_provider_http_to_ask_response(self):
        provider = Mock()
        provider.status_code = 200
        provider.json.return_value = {"choices": [{"message": {"content": json.dumps(DIRTY_ADVISOR)}}]}
        with patch.object(startsmart.requests, "post", return_value=provider) as post:
            response = startsmart.app.test_client().post("/ask", json={"question": "Which risk should I test first?"})
        self.assertEqual(post.call_args.kwargs["json"]["response_format"], {"type": "json_object"})
        self.assertEqual(response.headers["X-StartSmart-Advisor"], "structured-v2")
        answer = response.get_json()["answer"]
        self.assertEqual(answer, {"title": "Test customer demand first", "summary": "No new evidence.",
            "points": [{"title": "Demand:", "text": "Interview five potential customers."}],
            "next_action": "Record interviews.", "caution": "Regulatory requirements are unverified."})

    def test_nested_entities_all_fields_and_all_success_paths(self):
        dirty = deepcopy(DIRTY_ADVISOR)
        for _ in range(7):
            dirty = json.loads(json.dumps(dirty).replace("&", "&amp;"))
        with patch.object(startsmart, "call_groq", return_value=json.dumps(dirty)):
            response = startsmart.app.test_client().post("/ask", json={"question": "How to test?"})
        self.assertEqual(response.get_json()["answer"]["points"][0]["text"], "Interview five potential customers.")
        for question in ("", "What permits might I need?"):
            response = startsmart.app.test_client().post("/ask", json={"question": question})
            self.assertEqual(response.headers["X-StartSmart-Advisor"], "structured-v2")

    def test_context_segments_and_cautious_benefit(self):
        plan = example_plan()
        self.assertEqual([p["name"] for p in plan["customer_personas"]],
                         ["Daily commuters", "Ride-hailing drivers", "Fleet / company vehicle managers"])
        self.assertIn("Potential benefit to test", plan["idea_overview"]["impact"])
        self.assertNotIn("injury", plan["idea_overview"]["impact"])
        specific = [{"name": n} for n in ("Long-distance taxi drivers", "Delivery van drivers", "Company fleet buyers")]
        self.assertEqual(startsmart._segment_names("Car consulting", "", "", "en", specific), [p["name"] for p in specific])
        self.assertIn("Office lunch buyers", startsmart._segment_names("Lunch catering", "", "", "en"))

    def test_english_pdf_portable_punctuation(self):
        pdf = startsmart.build_pdf(example_plan(), "en")
        reader = PdfReader(pdf)
        text = "\n".join(page.extract_text() for page in reader.pages)
        for bad in ("■", "\ufffd", "\u2011"):
            self.assertNotIn(bad, text)
        for expected in ("Mobile Car-Interior Ergonomic Consulting", "ride-hailing", "face-to-face"):
            self.assertIn(expected, text)

    def test_arabic_export_localizes_english_defaults_without_mutation(self):
        plan = example_plan()
        before = deepcopy(plan)
        arabic = startsmart._localize_pdf_plan(plan, "ar")
        self.assertEqual(plan, before)
        self.assertEqual(arabic["business_name_suggestion"], plan["business_name_suggestion"])
        self.assertEqual(arabic["founder_passport"]["status"], "جاهز للتحقق، لا للتشغيل")
        self.assertEqual(arabic["seven_day_plan"][0]["focus"], "حدد العميل المستهدف")
        self.assertEqual(arabic["customer_personas"][0]["name"], "المتنقلون يومياً")
        self.assertTrue(all(any("\u0600" <= c <= "\u06ff" for c in d["success_check"]) for d in arabic["seven_day_plan"]))
        self.assertEqual(arabic["risk_radar"][0]["name"], "طلب العملاء")
        self.assertEqual(arabic["steps"][0]["estimated_cost_aed"], plan["steps"][0]["estimated_cost_aed"])
        pdf = startsmart.build_pdf(plan, "ar")
        reader = PdfReader(pdf)
        text = "\n".join(page.extract_text() for page in reader.pages)
        for bad in ("■", "\ufffd", "AI ESTIMATE", "USER INPUT", "Define target customer", "Ready to validate", "Customer Demand"):
            self.assertNotIn(bad, text)
        self.assertTrue(any("Amiri" in str(font.get_object().get("/BaseFont"))
                            for page in reader.pages for font in page["/Resources"]["/Font"].values()))

    def test_arabic_export_preserves_entered_proof(self):
        plan = example_plan()
        plan["proof_summary"] = {"total_responses": 3, "actual_payments": 1, "avg_price": 40}
        plan["decision_engine"]["decision"] = "Review pilot evidence"
        arabic = startsmart._localize_pdf_plan(plan, "ar")
        self.assertEqual(arabic["proof_summary"], plan["proof_summary"])
        self.assertEqual(arabic["decision_engine"]["decision"], "Review pilot evidence")
        self.assertNotIn("لم تُجمع", arabic["risk_radar"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
