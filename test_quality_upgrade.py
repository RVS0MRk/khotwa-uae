"""Bilingual plan, provenance and PDF regressions with a mocked provider."""
import json
import os
import unittest
import unicodedata
from copy import deepcopy
from unittest.mock import patch

from pypdf import PdfReader

os.environ["GROQ_API_KEY"] = "test-only-placeholder"
import app as khotwa


class QualityUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.client = khotwa.app.test_client()

    def generate(self, idea, category, region, budget, lang="en", raw=None):
        model = raw or {
            "business_name_suggestion": "Suggested Test Brand",
            "summary": "An unverified proposed service for local customers.",
            "idea_overview": {"problem": "Customers may have an inconvenient current option.",
                              "solution": "A simpler proposed service to test."},
            "readiness_report": {"target_customer": "Local potential buyers",
                                 "estimated_first_test_cost_aed": 100},
            "steps": [{"step_number": i + 1, "estimated_cost_aed": 0} for i in range(7)],
        }
        with patch.object(khotwa, "call_groq", return_value=json.dumps(model, ensure_ascii=False)) as mock:
            response = self.client.post("/generate", json={"idea": idea, "category": category,
                "region": region, "budget": budget, "lang": lang})
        self.assertEqual(response.status_code, 200)
        mock.assert_called_once()
        return response.get_json()

    def test_three_unrelated_businesses_have_localized_distinct_personas_and_risks(self):
        profiles = [
            ("AI website builder", "Technology & Digital", "Abu Dhabi", "data handling"),
            ("Healthy meal service", "Food & Catering", "Dubai", "Meal preparation"),
            ("Mobile car wash", "Services & Maintenance", "Sharjah", "Travel time"),
        ]
        needs = []
        for idea, category, region, execution_word in profiles:
            with self.subTest(idea=idea):
                plan = self.generate(idea, category, region, 5000)
                alternate = plan["_alternate_plan"]
                self.assertEqual((plan["_content_lang"], alternate["_content_lang"]), ("en", "ar"))
                self.assertEqual(plan["state"]["idea"], alternate["state"]["idea"])
                self.assertEqual(plan["state"]["user_budget_aed"], alternate["state"]["user_budget_aed"])
                self.assertEqual(plan["opportunity_score"]["total"], alternate["opportunity_score"]["total"])
                self.assertEqual(plan["total_timeline_days"], sum(s["timeline_days"] for s in plan["steps"]))
                self.assertIn(execution_word, plan["risk_radar"][3]["reason"])
                self.assertEqual(len({p["ask"] for p in plan["customer_personas"]}), 3)
                self.assertTrue(all(p["source"] == "ai_assumption" for p in plan["customer_personas"]))
                self.assertTrue(all("current_alternative" in p and "why_benefit" in p for p in plan["customer_personas"]))
                for path in khotwa._BILINGUAL_PATHS.values():
                    value = khotwa._plan_path(alternate, path)
                    self.assertTrue(khotwa._language_matches(value, "ar", idea), (path, value))
                needs.append(plan["customer_personas"][0]["potential_need"])
        self.assertEqual(len(set(needs)), 3)

    def test_bilingual_model_fields_preserve_meaning_and_reject_wrong_language(self):
        raw = {"summary": "A proposed digital scheduling service.",
               "idea_overview": {"problem": "Bookings may be hard to coordinate.",
                                 "solution": "A scheduling tool to test."},
               "readiness_report": {"target_customer": "Small business owners"},
               "bilingual_text": {
                   "en": {"summary": "A proposed booking tool for small businesses."},
                   "ar": {"summary": "أداة مقترحة لتنظيم الحجوزات لدى الشركات الصغيرة.",
                          "problem": "English-only wrong-language field",
                          "solution": "أداة لتنظيم الحجوزات تحتاج إلى اختبار."}}}
        plan = self.generate("Booking tool", "Technology & Digital", "Al Ain", 3000, raw=raw)
        self.assertEqual(plan["summary"], raw["bilingual_text"]["en"]["summary"])
        ar = plan["_alternate_plan"]
        self.assertEqual(ar["summary"], raw["bilingual_text"]["ar"]["summary"])
        self.assertEqual(ar["idea_overview"]["solution"], raw["bilingual_text"]["ar"]["solution"])
        self.assertNotIn("English-only", ar["idea_overview"]["problem"])
        self.assertEqual(ar["_localization_status"], "fallback")

    def test_advisor_multi_part_recall_and_user_budget_source(self):
        plan = self.generate("Meal planning app", "Technology & Digital", "Dubai", 5000)
        history = [{"role": "assistant", "content": json.dumps({"next_action": "Ask office managers about current scheduling."})}]
        with patch.object(khotwa, "call_groq") as mock:
            response = self.client.post("/ask", json={"question": "Recall your previous suggestion, my idea, budget, market and evidence status",
                "plan_context": plan, "history": history, "lang": "en"})
        self.assertEqual(response.status_code, 200)
        mock.assert_not_called()
        points = {p["title"]: p["text"] for p in response.get_json()["answer"]["points"]}
        self.assertEqual(len(points), 5)
        self.assertIn("Meal planning app", points["Business idea"])
        self.assertIn("AED 5,000 — USER INPUT", points["Budget"])
        self.assertEqual(points["Market"], "Dubai")
        self.assertIn("outside this app is unknown", points["Evidence"])
        self.assertIn("Ask office managers", points["Previous suggestion"])

    def test_advisor_relabels_budget_and_rejects_fictional_leads(self):
        plan = self.generate("Website builder", "Technology & Digital", "Abu Dhabi", 5000)
        answer = {"title": "Budget check", "summary": "AED 5,000 (AI estimate; verify supplier quotes.)",
                  "points": [{"title": "Source", "text": "The founder entered AED 5,000 (AI estimate)."}],
                  "next_action": "Ask potential customers what they use now.", "caution": ""}
        with patch.object(khotwa, "call_groq", return_value=json.dumps(answer)):
            response = self.client.post("/ask", json={"question": "What is my budget?", "plan_context": plan})
        self.assertEqual(response.status_code, 200)
        text = json.dumps(response.get_json()["answer"])
        self.assertIn("USER INPUT", text)
        self.assertNotIn("AI estimate", text)
        bad = deepcopy(answer)
        bad["summary"] = "Contact the three identified leads you spoke with."
        with patch.object(khotwa, "call_groq", return_value=json.dumps(bad)):
            response = self.client.post("/ask", json={"question": "Find first customers", "plan_context": plan})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("identified leads", json.dumps(response.get_json()["answer"]))

    def test_advisor_wrong_language_uses_matching_language_fallback(self):
        english = {"title": "Test demand", "summary": "Ask potential customers about their alternatives.",
                   "points": [{"title": "Interview", "text": "Record only conversations that actually occur."}],
                   "next_action": "Write down genuine answers.", "caution": ""}
        with patch.object(khotwa, "call_groq", return_value=json.dumps(english)):
            response = self.client.post("/ask", json={"question": "ما الخطوة التالية؟", "lang": "ar"})
        self.assertEqual(response.status_code, 200)
        answer = response.get_json()["answer"]
        self.assertTrue(khotwa._language_matches(json.dumps(answer, ensure_ascii=False), "ar"))
        self.assertNotEqual(answer["title"], english["title"])

    def test_discovery_rejects_wrong_language_cards(self):
        cards = {"ideas": [{"name": "English idea", "fit": "Matches skills", "customer": "Local customers",
                            "first_test": "Ask users", "assumption": "Need unverified", "category": "Other"} for _ in range(3)]}
        with patch.object(khotwa, "call_groq", return_value=json.dumps(cards)):
            response = self.client.post("/discover", json={"lang": "ar"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {"error": "discovery_unavailable"})

    def test_pdf_languages_keep_latest_proof_and_long_idea(self):
        idea = "Long digital workflow concept for independent restaurants and neighbourhood cafés " * 2
        plan = self.generate(idea, "Technology & Digital", "Dubai", 1500)
        plan["proof_summary"] = {"total_responses": 2, "avg_price": 26.5, "actual_payments": 0}
        plan["state"]["evidence"] = {"status": "customer_evidence", "responses": 2}
        before = deepcopy(plan)
        for lang in ("en", "ar"):
            with self.subTest(lang=lang):
                reader = PdfReader(khotwa.build_pdf(plan, lang))
                self.assertGreaterEqual(len(reader.pages), 3)
                text = "\n".join(page.extract_text() for page in reader.pages)
                self.assertIn("26.5", text)
                self.assertIn("2", text)
                self.assertIn("Khotwa" if lang == "en" else "خطوة", unicodedata.normalize("NFKC", text))
        self.assertEqual(plan, before)


if __name__ == "__main__":
    unittest.main()
