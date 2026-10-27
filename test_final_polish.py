"""Targeted final correctness regressions, using only mocked provider output."""
import json
import os
import unittest
from copy import deepcopy
from unittest.mock import patch
from pypdf import PdfReader

os.environ["GROQ_API_KEY"] = "test-only-placeholder"
import app as startsmart

KEYS = ("local_fit", "clear_customer", "low_starting_cost", "easy_first_step", "growth_potential")


def model_plan(costs=(0, 0, 0, 0, 100, 300, 0)):
    return {"business_name_suggestion": "Content service", "summary": "A planning assumption.",
            "steps": [{"step_number": i+1, "action": "Validation", "estimated_cost_aed": cost} for i, cost in enumerate(costs)],
            "total_estimated_cost_aed": 5000, "readiness_report": {"target_customer": "Restaurant owners/marketing managers with 1-20 seats"}}


class FinalPolishTests(unittest.TestCase):
    def generate(self, raw, idea="Social-media content service", budget=200, lang="en"):
        with patch.object(startsmart, "call_groq", return_value=json.dumps(raw)):
            response = startsmart.app.test_client().post("/generate", json={"idea": idea, "budget": budget, "lang": lang})
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def test_step_cost_total_and_gap_are_authoritative(self):
        plan = self.generate(model_plan())
        self.assertEqual(plan["total_estimated_cost_aed"], 400)
        self.assertEqual(plan["estimated_budget_gap_aed"], 200)
        self.assertEqual(plan["readiness_report"]["estimated_setup_cost_aed"], 400)
        self.assertEqual(sum(s["estimated_cost_aed"] for s in plan["steps"]), 400)
        self.assertEqual(self.generate(model_plan(), budget=2000)["estimated_budget_gap_aed"], 0)

    def test_unknown_invalid_and_zero_costs_are_distinct(self):
        for invalid in (None, "", "unknown", "100-200", -20, True, float("inf")):
            with self.subTest(invalid=invalid):
                plan = self.generate(model_plan([0, 0, 0, 0, 100, invalid, 0]))
                self.assertIsNone(plan["total_estimated_cost_aed"])
                self.assertIsNone(plan["estimated_budget_gap_aed"])
        zero = self.generate(model_plan([0]*7))
        self.assertEqual(zero["total_estimated_cost_aed"], 0)
        decimal = self.generate(model_plan([0, 0, 0, 0, 23.25, 30.5, 0]))
        self.assertEqual(decimal["total_estimated_cost_aed"], 53.75)

    def test_two_businesses_keep_distinct_reasoned_model_scores(self):
        examples = [
            ("Social-media content service", [4, 3, 5, 4, 3], ["Founder has restaurant content experience", "Restaurants' willingness to change suppliers is unknown", "Content interviews need few tools", "A sample content calendar can be shown this week", "Client approvals limit content capacity"]),
            ("Cold-chain delivery fleet", [2, 4, 1, 2, 4], ["Founder lacks refrigerated fleet experience", "Perishable-goods buyers have a defined delivery problem", "Refrigerated vehicles exceed the entered budget", "Cold-chain logistics need careful preparation", "Repeat delivery routes may support expansion"])]
        outputs = []
        for idea, values, reasons in examples:
            raw = model_plan()
            raw["opportunity_score"] = {key: {"score": value, "reason": reason} for key, value, reason in zip(KEYS, values, reasons)}
            score = self.generate(raw, idea)["opportunity_score"]
            self.assertEqual([score[key]["score"] for key in KEYS], values)
            self.assertEqual(score["total"], sum(values))
            self.assertEqual(score["source"], "ai_assumption")
            self.assertTrue(all(score[key]["reason"] for key in KEYS))
            outputs.append(values)
        self.assertNotEqual(outputs[0], outputs[1])
        fallback = self.generate(model_plan())["opportunity_score"]
        self.assertEqual(fallback["source"], "fallback_or_mixed")
        self.assertTrue(all(fallback[key]["source"] == "fallback" for key in KEYS))
        self.assertNotIn('"total": 19', startsmart.SCHEMA)

    def test_contextual_execution_risk_and_customer_wording(self):
        for idea, expected in (("Social-media content service", "Content-production"),
                               ("Mobile car wash", "Travel time"),
                               ("Digital scheduling software", "Development effort")):
            with self.subTest(idea=idea):
                plan = self.generate(model_plan(), idea)
                self.assertIn(expected, plan["risk_radar"][3]["reason"])
                self.assertIn("unverified", plan["risk_radar"][4]["reason"])
        plan = self.generate(model_plan())
        expected = "Owners or marketing managers of small independent restaurants with roughly 1-20 seats."
        self.assertEqual(plan["readiness_report"]["target_customer"], expected)
        self.assertEqual(plan["state"]["target_customer_source"], "ai_assumption")
        self.assertEqual(plan["state"]["target_customer"], expected)

    def test_pdf_recomputes_stale_total_preserves_fractional_proof(self):
        plan = self.generate(model_plan())
        plan["total_estimated_cost_aed"] = 5000  # Old browser state must not bypass derivation.
        plan["proof_summary"] = {"total_responses": 2, "avg_price": 26.5}
        before = deepcopy(plan)
        for language in ("en", "ar"):
            reader = PdfReader(startsmart.build_pdf(plan, language))
            text = "\n".join(page.extract_text() for page in reader.pages)
            self.assertNotIn("5,000", text)
            self.assertIn("400", text)
            self.assertIn("26.5", text)
            self.assertNotIn("■", text)
        self.assertEqual(plan, before)
        unknown = self.generate(model_plan([None]*7))
        text = "\n".join(page.extract_text() for page in PdfReader(startsmart.build_pdf(unknown)).pages)
        self.assertIn("Not estimated yet", text)
        self.assertIn("Estimated gap: Not available", text)
