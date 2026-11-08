"""Rich model content must survive; unsupported claims must not."""

import json
import re
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from test_support import configure_mock_environment

configure_mock_environment()
import app
from content_safety import safe_text
from plan_content import PITCH_LIMITS

FIXTURES = Path(__file__).parent / "tests" / "fixtures"


def fixture(name="rich_plan_en"):
    return json.loads((FIXTURES / (name + ".json")).read_text(encoding="utf-8"))


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, child in value.items():
            if key != "bilingual_text":
                yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)


def normalized(name, lang="en"):
    raw = fixture(name)
    return app._normalize_plan(
        raw,
        {
            "idea": fixture()["summary"] if name == "unsafe_plan_en" else raw["summary"],
            "budget": 5000,
            "region": "Sharjah" if "alt" in name else "Abu Dhabi",
        },
        lang,
    )


class ContentTests(unittest.TestCase):
    def test_advisor_keeps_safe_personalized_sentences_and_approval_topics(self):
        answer = {
            "title": "Lunch box offer test",
            "summary": "Ask office workers about their lunch routine. Research shows 80% demand. Compare pickup windows.",
            "points": [{"title": "Before selling", "text": "Check what approvals apply before selling."}],
            "next_action": "Draft a deposit-free lunch waitlist message.",
            "caution": "",
        }
        result = app._parse_advisor(json.dumps(answer), "en")
        self.assertEqual(result["summary"], "Ask office workers about their lunch routine. Compare pickup windows.")
        self.assertEqual(result["points"], answer["points"])
        self.assertEqual(result["next_action"], answer["next_action"])

    def test_rich_retention_over_75_percent_in_both_languages(self):
        for name, lang in [("rich_plan_en", "en"), ("rich_plan_alt_en", "en"), ("rich_plan_ar", "ar")]:
            before = list(strings(fixture(name)))
            after = set(strings(normalized(name, lang)))
            ratio = sum(s in after for s in before) / len(before)
            self.assertGreaterEqual(ratio, 0.75, (name, ratio))

    def test_different_businesses_keep_different_personalized_guidance(self):
        a, b = normalized("rich_plan_en"), normalized("rich_plan_alt_en")
        for key in ("first_step_today", "validation_questions", "pitches"):
            self.assertNotEqual(a[key], b[key], key)
        self.assertNotEqual([d["action"] for d in a["seven_day_plan"]], [d["action"] for d in b["seven_day_plan"]])

    def test_removes_only_unsafe_sentences_and_keeps_neighbours(self):
        p = normalized("unsafe_plan_en")
        text = json.dumps(p, ensure_ascii=False)
        for bad in ("Research shows", "80%", "DED", "15,000", "Collect deposits", "<script>", "alert("):
            self.assertNotIn(bad, text)
        for good in (
            "A weekly menu could simplify lunch choices.",
            "Flexible ingredients are an assumption to test.",
            "A weekly menu is a proposed offer.",
            "Flexible collection is worth testing.",
            "Delivery timing needs testing.",
            "Ask office workers about their lunch break.",
        ):
            self.assertIn(good, text)

    def test_claim_filters_allow_topics_and_hypotheses(self):
        allowed = [
            "Customers pre-order lunch boxes weekly",
            "A subscription with a 10% first-month discount is a pricing hypothesis",
            "Check what approvals apply before selling",
            "This looks promising if interviews confirm demand",
        ]
        for text in allowed:
            self.assertEqual(safe_text(text), text)
        for text in [
            "Research shows 80% demand.",
            "Customers said they love it.",
            "You must obtain a DED licence (AED 15,000).",
            "Take deposits now.",
            "Start operating the service this week.",
        ]:
            self.assertEqual(safe_text(text), "", text)

    def test_structural_repair_is_positional_and_preserves_safe_slots(self):
        raw = fixture()
        raw["seven_day_plan"] = raw["seven_day_plan"][:2]
        raw["validation_questions"] = raw["validation_questions"][:3]
        raw["risk_radar"][0]["level"] = "Low"
        p = app._normalize_plan(raw, {"idea": "DeskFresh lunches", "budget": 5000}, "en")
        self.assertEqual(len(p["seven_day_plan"]), 7)
        self.assertEqual([x["day"] for x in p["seven_day_plan"]], list(range(1, 8)))
        self.assertEqual(p["seven_day_plan"][1]["action"], raw["seven_day_plan"][1]["action"])
        self.assertEqual(len(p["validation_questions"]), 5)
        self.assertEqual(len(p["risk_radar"]), 5)
        self.assertEqual(p["risk_radar"][0]["level"], "Medium")
        self.assertEqual(len(p["steps"]), 7)

    def test_empty_descriptions_are_honest_missing_labels(self):
        raw = fixture()
        raw["idea_overview"]["solution"] = "Take deposits now."
        raw["summary"] = "Research shows 80% demand."
        p = app._normalize_plan(raw, {"idea": "DeskFresh lunches"}, "en")
        for value in (p["summary"], p["idea_overview"]["solution"]):
            self.assertEqual(value, "Not provided — describe it in Edit idea")

    def test_pitch_limits_and_seams_in_both_languages(self):
        for name, lang in [("rich_plan_en", "en"), ("rich_plan_alt_en", "en"), ("rich_plan_ar", "ar")]:
            p = normalized(name, lang)
            for key, limit in PITCH_LIMITS.items():
                self.assertLessEqual(len(p["pitches"][key].split()), limit)
            text = "\n".join(strings(p))
            self.assertNotRegex(text, r" is Start with| facing [A-Z]|\.\.|\.[A-Z]")
            self.assertNotRegex(p["whatsapp_message"], r"^(Khotwa|خطوة)\s*[—–-]")
        p = normalized("rich_plan_en")
        p["pitches"] = {}
        app._compose_pitches(p, "en")
        self.assertNotIn(" in Abu Dhabi in Abu Dhabi", " ".join(p["pitches"].values()))

    def test_discovery_keeps_three_distinct_tests(self):
        ideas = [
            {
                "name": f"Distinct concept {i}",
                "fit": "Uses the founder teaching skills",
                "customer": "Local students",
                "first_test": f"Interview {i+3} students about topic {i} without selling.",
                "assumption": f"Assumption {i}: students need a different way to practise.",
                "category": "Education & Tutoring",
            }
            for i in range(3)
        ]
        with patch.object(app, "call_groq", return_value=json.dumps({"ideas": ideas})):
            result = app.app.test_client().post("/discover", json={"skills": "Teaching", "budget": 1000})
        self.assertEqual(result.status_code, 200)
        self.assertEqual([i["first_test"] for i in result.json["ideas"]], [i["first_test"] for i in ideas])

    def test_route_retains_primary_rich_fields(self):
        raw = fixture()
        with patch.object(app, "call_groq", return_value=json.dumps(raw)):
            r = app.app.test_client().post("/generate", json={"idea": raw["summary"], "region": "Abu Dhabi"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["pitches"], raw["pitches"])
        self.assertEqual(r.json["idea_overview"]["solution"], raw["idea_overview"]["solution"])
