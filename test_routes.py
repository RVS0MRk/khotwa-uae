"""Local route checks that do not contact Groq or read the project key."""

import os
import json
import unittest
from unittest.mock import patch

os.environ["GROQ_API_KEY"] = "test-only-placeholder"

import app as startsmart


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.client = startsmart.app.test_client()

    def test_money_parsing_preserves_magnitude(self):
        self.assertEqual(startsmart._int("AED 4,000.50"), 4000)
        self.assertEqual(startsmart._int("300-500"), 0)
        self.assertEqual(startsmart._int(float("inf")), 0)

    def test_generate_passes_market_and_context(self):
        with patch.object(startsmart, "call_groq", return_value='{"opportunity_score":{"total":15}}') as mock:
            response = self.client.post("/generate", json={
                "idea": "Mobile car wash", "category": "Services", "user_type": "residents",
                "budget": 4000, "region": "Abu Dhabi", "context": "Local service", "lang": "en",
            })
        self.assertEqual(response.status_code, 200)
        system, user = mock.call_args.args[:2]
        self.assertIn("Abu Dhabi", system)
        self.assertIn("Local service", system)
        self.assertIn("Abu Dhabi", user)
        self.assertIn("4000 AED", user)
        self.assertIn("never", system.lower())
        state = response.get_json()["state"]
        self.assertEqual(state["user_budget_aed"], 4000)
        self.assertEqual(state["category"], "Services")
        self.assertEqual(state["region"], "Abu Dhabi")
        self.assertEqual(state["evidence"]["status"], "not_validated")

    def test_ask_uses_plan_and_recent_history(self):
        plan = {
            "readiness_report": {"idea": "Mobile car wash", "target_customer": "Apartment residents",
                                 "main_risk": "Finding paying users", "next_step": "Run a paid pilot"},
            "opportunity_score": {"total": 18}, "_region": "Abu Dhabi", "_context": "Local service",
            "_budget": 4000, "proof_summary": {"interested": 5, "pre_orders": 2},
            "risk_radar": [{"name": "Customer Demand", "reason": "Price is untested"}],
        }
        history = [{"role": "user", "content": "Who should I ask?"},
                   {"role": "assistant", "content": "Ask apartment residents."}]
        structured = {"title": "Customer risks", "summary": "Test demand first.",
                      "points": [{"title": "Channel", "text": "Ask apartment residents."}],
                      "next_action": "Collect no-payment reservations.", "caution": "Verify approvals."}
        with patch.object(startsmart, "call_groq", return_value=json.dumps(structured)) as mock:
            response = self.client.post("/ask", json={"question": "What are my risks?",
                                                        "lang": "en", "plan_context": plan,
                                                        "history": history})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["answer"], structured)
        system, question = mock.call_args.args[:2]
        self.assertEqual(question, "What are my risks?")
        for detail in ("Mobile car wash", "Abu Dhabi", "Local service", "4000", "18", "pre_orders", "Run a paid pilot"):
            self.assertIn(detail, system)
        self.assertIn("Never invent", system)
        self.assertEqual(mock.call_args.kwargs["history"], history)
        self.assertTrue(mock.call_args.kwargs["json_mode"])
        self.assertIn("Return exactly one JSON object", system)

    def test_regulatory_answer_and_plan_guard(self):
        with patch.object(startsmart, "call_groq") as mock:
            answer = self.client.post("/ask", json={"question": "Do I need a water permit?",
                                                    "plan_context": {"_region": "Dubai"}})
        self.assertEqual(answer.status_code, 200)
        self.assertIn("have not been verified", answer.get_json()["answer"]["summary"])
        self.assertIn("relevant UAE authority", answer.get_json()["answer"]["summary"])
        mock.assert_not_called()

        invented = {"opportunity_score": {"total": 15},
                    "risk_radar": [{"name": "Legal risk", "level": "High",
                                    "reason": "A Water Use Permit is required.", "fix": "Pay the fee."}],
                    "steps": [{"action": "Obtain a Water Use Permit", "description": "Pay the permit fee.",
                               "estimated_cost_aed": 999, "timeline_days": 30}]}
        with patch.object(startsmart, "call_groq", return_value=json.dumps(invented)):
            response = self.client.post("/generate", json={"idea": "Mobile car wash", "region": "Dubai"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Water Use Permit", response.get_data(as_text=True))
        self.assertIsNone(response.get_json()["steps"][0]["estimated_cost_aed"])

    def test_health_and_malformed_advisor_response(self):
        with patch.object(startsmart, "call_groq") as mock:
            health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json(), {"status": "ok"})
        mock.assert_not_called()
        with patch.object(startsmart, "call_groq", return_value="```bad output```"):
            response = self.client.post("/ask", json={"question": "How do I test?"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Next validation step", response.get_json()["answer"]["title"])
        noisy = {"title": "### Pricing", "summary": "Use **a test**<br>first.",
                 "points": [{"title": "Step", "text": "Ask customers\\| now"}],
                 "next_action": "Create a waitlist", "caution": ""}
        with patch.object(startsmart, "call_groq", return_value=json.dumps(noisy)):
            response = self.client.post("/ask", json={"question": "Pricing test"})
        answer = response.get_json()["answer"]
        self.assertEqual(answer["title"], "Pricing")
        self.assertEqual(answer["summary"], "Use a test first.")
        self.assertEqual(answer["points"][0]["text"], "Ask customers now")

    def test_advisor_decodes_entities_and_removes_model_formatting(self):
        noisy = {
            "title": "### &#x41;dvisor **tip**",
            "summary": "Use &amp;#x55;AE interviews<br>before a &lt;b&gt;pilot&lt;/b&gt;.",
            "points": [{"title": "**First**", "text": "Ask &#x35; customers\\| then use [a waitlist](https://example.test)."}],
            "next_action": "`Record` their answers.",
            "caution": "Avoid &#x20; payments before checking approvals."
        }
        with patch.object(startsmart, "call_groq", return_value=json.dumps(noisy)):
            response = self.client.post("/ask", json={"question": "How should I test?"})
        self.assertEqual(response.status_code, 200)
        answer = response.get_json()["answer"]
        self.assertEqual(answer, {
            "title": "Advisor tip", "summary": "Use UAE interviews before a pilot.",
            "points": [{"title": "First", "text": "Ask 5 customers then use a waitlist."}],
            "next_action": "Record their answers.",
            "caution": "Avoid payments before checking approvals."
        })
        for marker in ("###", "**", "&#", "<br", "<b", "`", "\\|", "[a waitlist]"):
            self.assertNotIn(marker, response.get_data(as_text=True))

    def test_advisor_rejects_malformed_shapes_and_embedded_json(self):
        base = {"title": "Good", "summary": "A useful answer.",
                "points": [{"title": "Step", "text": "Ask customers."}],
                "next_action": "Start interviews.", "caution": ""}
        cases = [
            {**base, "points": [{"title": "Step", "text": {"raw": "JSON"}}]},
            {**base, "summary": '{"title":"raw","summary":"do not show"}'},
            {**base, "summary": 'Advice: {"internal": "do not show"}'},
            {**base, "next_action": "Return only JSON"},
            {**base, "points": "not a list"},
        ]
        for malformed in cases:
            with self.subTest(malformed=malformed), patch.object(startsmart, "call_groq", return_value=json.dumps(malformed)):
                response = self.client.post("/ask", json={"question": "What next?"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get_json()["answer"], startsmart._advisor_fallback("en"))

    def test_advisor_arabic_entities_are_decoded(self):
        answer = {"title": "### نصيحة", "summary": "ابدأ &#x628;مقابلات العملاء.",
                  "points": [{"title": "**اختبار**", "text": "اسأل خمسة عملاء<br>اليوم."}],
                  "next_action": "سجل الإجابات.", "caution": ""}
        with patch.object(startsmart, "call_groq", return_value=json.dumps(answer, ensure_ascii=False)):
            response = self.client.post("/ask", json={"question": "كيف أختبر الفكرة؟", "lang": "ar"})
        self.assertEqual(response.status_code, 200)
        cleaned = response.get_json()["answer"]
        self.assertEqual(cleaned["title"], "نصيحة")
        self.assertEqual(cleaned["summary"], "ابدأ بمقابلات العملاء.")
        self.assertEqual(cleaned["points"][0]["text"], "اسأل خمسة عملاء اليوم.")

    def test_discovery_requires_exactly_three_structured_ideas(self):
        idea = {"name": "Local service", "fit": "Matches skills", "customer": "Residents",
                "first_test": "Ask five residents", "assumption": "Residents need this"}
        with patch.object(startsmart, "call_groq", return_value=json.dumps({"ideas": [idea] * 3})):
            response = self.client.post("/discover", json={"skills": "cleaning", "budget": 4000})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()["ideas"]), 3)
        with patch.object(startsmart, "call_groq", return_value=json.dumps({"ideas": [idea]})):
            response = self.client.post("/discover", json={"skills": "cleaning"})
        self.assertEqual(response.status_code, 503)

    def test_generated_claims_are_not_treated_as_evidence(self):
        invented = {"idea_overview": {"evidence": "30% of surveyed drivers want this."},
                    "readiness_report": {"target_customer": "Residents", "estimated_first_test_cost_aed": 300},
                    "summary": "Initial interviews suggest interest", "opportunity_score": {"total": 25},
                    "decision_engine": {"decision": "Run a small pilot"}}
        with patch.object(startsmart, "call_groq", return_value=json.dumps(invented)):
            response = self.client.post("/generate", json={"idea": "Mobile car wash", "category": "Services & Maintenance", "budget": 4000, "region": "Abu Dhabi", "context": "Local service"})
        plan = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("surveyed", response.get_data(as_text=True))
        self.assertEqual(plan["state"]["user_budget_aed"], 4000)
        self.assertEqual(plan["state"]["category"], "Services & Maintenance")
        self.assertEqual(plan["state"]["evidence"]["status"], "not_validated")
        self.assertEqual(plan["decision_engine"]["decision"], "Validate more")

    def test_plan_safety_budget_and_evidence_across_sections(self):
        unsafe = {"summary": "Initial interviews suggest strong demand.",
                  "idea_overview": {"impact": "Equipment can be sourced under AED 2,000"},
                  "readiness_report": {"main_risk": "mobile water-use permits", "estimated_first_test_cost_aed": 200},
                  "risk_radar": [{"name": "Regulation", "reason": "waste-disposal permits"}],
                  "small_test_plan": {"points": ["Offer free washes", "Schedule actual service"]},
                  "steps": [{"action": "Get required mobile-service permits", "description": "Map permit requirements"}],
                  "founder_passport": {"next_step": "Run micro-pilot washes"},
                  "pitches": {"ten_sec": "Proven water savings for just AED 30"},
                  "proof_summary": {"total_responses": 10, "actual_payments": 8},
                  "decision_engine": {"decision": "Strong viable opportunity", "reason": "Score 19 shows promise"},
                  "suggested_test_price_aed": 30, "total_estimated_cost_aed": 5000}
        inputs = {"idea": "Mobile car wash", "category": "Services & Maintenance", "budget": 4000,
                  "region": "Abu Dhabi", "context": "Local service", "lang": "en"}
        with patch.object(startsmart, "call_groq", return_value=json.dumps(unsafe)):
            response = self.client.post("/generate", json=inputs)
        self.assertEqual(response.status_code, 200)
        p = response.get_json()
        text = json.dumps(p)
        for claim in ("water-use", "waste-disposal", "mobile-service permits", "micro-pilot", "free washes", "interviews suggest", "shows promise", "Proven water savings"):
            self.assertNotIn(claim, text)
        self.assertNotIn("proof_summary", p)
        self.assertEqual(p["state"]["evidence"]["responses"], 0)
        self.assertEqual(p["state"]["user_budget_aed"], 4000)
        self.assertIsNone(p["total_estimated_cost_aed"])
        self.assertIsNone(p["estimated_budget_gap_aed"])
        self.assertEqual(p["state"]["category"], inputs["category"])
        self.assertEqual(p["state"]["region"], inputs["region"])
        self.assertEqual(p["state"]["context"], inputs["context"])
        self.assertEqual(len({d["success_check"] for d in p["seven_day_plan"]}), 7)
        self.assertEqual(len(p["steps"]), 7)
        self.assertIn("After confirming", p["steps"][5]["description"])
        self.assertEqual(p["customer_personas"][0]["name"], "Residential car owners")
        self.assertEqual(p["decision_engine"]["decision"], "Validate more")
        self.assertIn("Price hypothesis: AED 30", p["pitches"]["thirty_sec"])
        self.assertIn("define the unit and scope", p["pitches"]["thirty_sec"])
        self.assertIn("AI ASSUMPTION", p["pitches"]["thirty_sec"])

    def test_exact_discovery_profile_produces_three_safe_cards(self):
        profile = {"skills": "AutoCAD, communication, basic engineering knowledge", "interests": "Cars and technology",
                   "experience": "University student", "budget": 4000, "region": "Abu Dhabi",
                   "context": "Local service or digital", "time_available": "10 hours/week", "lang": "en"}
        cards = [{"name": name, "fit": "Uses technical and communication skills", "customer": "Car owners",
                  "first_test": "Offer free washes", "assumption": "Strong demand", "category": "Services & Maintenance"}
                 for name in ("Car-care scheduling concept", "Vehicle reminder tool", "Car accessory research service")]
        with patch.object(startsmart, "call_groq", return_value=json.dumps({"ideas": cards})) as mock:
            response = self.client.post("/discover", json=profile)
        self.assertEqual(response.status_code, 200)
        ideas = response.get_json()["ideas"]
        self.assertEqual(len(ideas), 3)
        self.assertEqual(json.loads(mock.call_args.args[1])["context"], profile["context"])
        for idea in ideas:
            self.assertTrue(all(idea[k] for k in ("name", "fit", "customer", "first_test", "assumption")))
            self.assertIn("no-payment waitlist", idea["first_test"])
            self.assertNotIn("Strong demand", idea["assumption"])

    def test_final_advisor_cases_filter_unsupported_claims(self):
        noisy = {"title": "### Advice", "summary": "Get mobile water-use permits &#x20; first.",
                 "points": [{"title": "**Test**", "text": "Find paying customers with free washes."}],
                 "next_action": "Schedule a micro-pilot.", "caution": ""}
        for question in ("What are my biggest risks?", "Which risk should I test first?", "How do I find my first 3 customers?", "What licences or approvals might I need?"):
            with self.subTest(question=question), patch.object(startsmart, "call_groq", return_value=json.dumps(noisy)):
                response = self.client.post("/ask", json={"question": question, "plan_context": {"_region": "Abu Dhabi"}})
                self.assertEqual(response.status_code, 200)
                answer = response.get_json()["answer"]
                self.assertEqual(set(answer), {"title", "summary", "points", "next_action", "caution"})
                visible = " ".join([answer["title"], answer["summary"], answer["next_action"], answer["caution"]] + [x["text"] for x in answer["points"]])
                for bad in ("###", "**", "&#", "water-use", "free washes", "micro-pilot", "<br>"):
                    self.assertNotIn(bad, visible)
                if "3 customers" in question:
                    self.assertIn("three strong leads", answer["title"])
                    self.assertIn("not a paying customer", answer["summary"])
                if "approvals" in question:
                    self.assertIn("TAMM", answer["summary"])
                    self.assertIn("ADDED", answer["summary"])

    def test_malformed_generated_json_returns_safe_error(self):
        with patch.object(startsmart, "call_groq", return_value="```bad { model output"):
            response = self.client.post("/generate", json={"idea": "Mobile car wash"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json(), {"error": "generation_failed"})

    def test_api_errors_do_not_reach_browser(self):
        with patch.object(startsmart, "call_groq", side_effect=RuntimeError("secret model failure")):
            answer = self.client.post("/ask", json={"question": "Hi"})
            plan = self.client.post("/generate", json={"idea": "A shop"})
        self.assertEqual(answer.status_code, 503)
        self.assertEqual(plan.status_code, 500)
        self.assertNotIn("secret", answer.get_data(as_text=True))
        self.assertNotIn("secret", plan.get_data(as_text=True))

    def test_pdf_accepts_ai_text_as_text(self):
        response = self.client.post("/pdf", json={
            "business_name_suggestion": "A <b>shop</b>",
            "summary": "Test demand before setup",
            "opportunity_score": {"total": 15},
            "readiness_report": {"idea": "A <b>shop</b>"},
            "steps": [{"step_number": 1, "action": "Paid pilot", "description": "Test one sale",
                       "estimated_cost_aed": 100, "timeline_days": 2}],
            "total_estimated_cost_aed": 4000,
            "_region": "Dubai",
            "_lang": "en",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.startswith(b"%PDF"))

    def test_arabic_pdf_uses_bundled_font_without_network(self):
        sample = {"business_name_suggestion": "غسيل سيارات متنقل",
                  "summary": "فرضية للاختبار", "opportunity_score": {"total": 15},
                  "readiness_report": {"idea": "غسيل سيارات متنقل"},
                  "steps": [{"step_number": 1, "action": "مقابلات", "description": "اختبر الفكرة",
                             "estimated_cost_aed": 1, "timeline_days": 1}],
                  "_lang": "ar", "_region": "Abu Dhabi"}
        with patch.object(startsmart.urllib.request, "urlretrieve", side_effect=AssertionError("network font fetch")) as download:
            response = self.client.post("/pdf", json=sample)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.startswith(b"%PDF"))
        download.assert_not_called()


if __name__ == "__main__":
    unittest.main()
