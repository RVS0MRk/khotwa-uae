"""Cross-channel checks for achieved business outcomes; no provider traffic."""

import io
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
from test_v22_content import fixture
from test_v221_safety import at

REVIEW = json.loads((Path(__file__).parent / "tests/fixtures/v222_review.json").read_text(encoding="utf-8"))
FIELDS = [
    ("summary",),
    ("pitches", "thirty_sec"),
    ("first_step_today",),
    ("idea_overview", "why_market"),
    ("opportunity_score", "local_fit", "reason"),
]


def tagged(text, marker):
    return text.rstrip(".!?؟") + " " + marker + (text[-1] if text[-1] in ".!?؟" else ".")


class V222SafetyTests(unittest.TestCase):
    def setUp(self):
        transport = patch("requests.post", side_effect=AssertionError("Live Groq forbidden"))
        transport.start()
        self.addCleanup(transport.stop)

    def test_review_language_table_and_neighbour_preservation(self):
        for lang in ("en", "ar"):
            good = (
                "Interview office workers about their lunch routine."
                if lang == "en"
                else "اسأل موظفي المكاتب عن خيارات الغداء."
            )
            for kind in ("unsafe", "safe"):
                for text in REVIEW[kind + "_" + lang]:
                    with self.subTest(lang=lang, kind=kind, text=text):
                        self.assertEqual(safe_text(text, lang), text if kind == "safe" else "")
                        self.assertEqual(
                            safe_text(good + " " + text + " " + good, lang),
                            good + " " + (text + " " if kind == "safe" else "") + good,
                        )

    def test_all_review_cases_in_five_plan_fields_and_advisor_and_discovery(self):
        for lang in ("en", "ar"):
            raw = fixture("rich_plan_" + lang)
            good = (
                "Interview office workers about their lunch routine."
                if lang == "en"
                else "اسأل موظفي المكاتب عن خيارات الغداء."
            )
            for kind in ("unsafe", "safe"):
                for i, text in enumerate(REVIEW[kind + "_" + lang]):
                    with self.subTest(lang=lang, kind=kind, text=text):
                        for path in FIELDS:
                            dirty = deepcopy(raw)
                            at(dirty, path[:-1])[path[-1]] = good + " " + text
                            result = app._normalize_plan(dirty, {"idea": raw["summary"], "budget": 5000}, lang)
                            actual = at(result, path)
                            self.assertIn(good, actual)
                            if kind == "unsafe":
                                self.assertNotIn(text, json.dumps(result, ensure_ascii=False))
                            else:
                                self.assertIn(text, actual)
                        answer = {
                            "title": good,
                            "summary": good + " " + text,
                            "points": [{"title": good, "text": good + " " + text}],
                            "next_action": good + " " + text,
                            "caution": "",
                        }
                        with patch.object(app, "call_groq", return_value=json.dumps(answer)):
                            r = app.app.test_client().post(
                                "/ask", json={"question": "Suggest a next test", "lang": lang}
                            )
                        self.assertEqual(r.status_code, 200)
                        for actual in [
                            r.json["answer"]["summary"],
                            r.json["answer"]["points"][0]["text"],
                            r.json["answer"]["next_action"],
                        ]:
                            self.assertEqual(actual, good + (" " + text if kind == "safe" else ""))
                        card = {
                            "name": good,
                            "customer": good,
                            "category": "Food & Catering",
                            **{key: good + " " + text for key in ("fit", "first_test", "assumption")},
                        }
                        with patch.object(app, "call_groq", return_value=json.dumps({"ideas": [card] * 3})):
                            r = app.app.test_client().post(
                                "/discover", json={"skills": "Cooking", "budget": 1000, "lang": lang}
                            )
                        self.assertEqual(r.status_code, 200)
                        for key in ("fit", "first_test", "assumption"):
                            self.assertEqual(r.json["ideas"][0][key], good + (" " + text if kind == "safe" else ""))

    def test_predicate_object_combinations_and_local_guards(self):
        # Compositional checks do not depend on one full leaked sentence.
        for subject in ("Customers", "Subscribers", "Investors"):
            for action in ("paid for the service", "signed contracts", "joined the waitlist"):
                with self.subTest(subject=subject, action=action):
                    self.assertEqual(safe_text(f"{subject} have {action}."), "")
                    for lead in ("If", "Unless", "Check whether", "Ask whether"):
                        text = f"{lead} {subject.lower()} have {action}, record the actual evidence."
                        self.assertEqual(safe_text(text), text)
                    bad = f"If the draft is useful, {subject.lower()} have {action}."
                    self.assertEqual(safe_text(bad), "")
        for text in (
            "Our plan is already profitable.",
            "Buyers trust the service.",
            "The subscriptions reached their launch target.",
        ):
            self.assertEqual(safe_text(text), "")
        for text in (
            "Have customers paid for the service?",
            "Customers have never paid for the service.",
            "Our plan is to measure whether subscribers have signed contracts.",
        ):
            self.assertEqual(safe_text(text), text)
        for heading in ("Test the offer", "Review evidence", "Verify requirements"):
            self.assertEqual(safe_text(heading + " This idea is validated."), "")
        self.assertEqual(safe_text("Check whether this idea is validated."), "Check whether this idea is validated.")
        for text in ("اجمع حجوزات بلا دفع من المهتمين.", "نختبر قائمة الوجبات مع موظفين دون بيع أو دفع."):
            self.assertEqual(safe_text(text, "ar"), text)

    def test_founder_and_investment_pdf_text_extraction_for_each_review_case(self):
        from pypdf import PdfReader
        from test_finance import BASE

        # Latin markers in each sentence survive both RTL shaping and extraction.
        # A removed sentence cannot leave its marker; every safe marker must
        # appear. This avoids a false pass from searching logical Arabic in a
        # PDF whose Arabic text is stored as bidi presentation forms.
        for lang in ("en", "ar"):
            raw = fixture("rich_plan_" + lang)
            plan = app._normalize_plan(raw, {"idea": raw["summary"], "budget": 5000}, lang)
            good = (
                "Interview office workers about their lunch routine."
                if lang == "en"
                else "اسأل موظفي المكاتب عن خيارات الغداء."
            )
            all_sentences = []
            markers = {}
            for kind in ("unsafe", "safe"):
                for i, text in enumerate(REVIEW[kind + "_" + lang]):
                    mark = ("LEAK" if kind == "unsafe" else "KEEP") + str(i + 100)
                    all_sentences.append(tagged(text, mark))
                    markers[mark] = kind
            body = good + " " + " ".join(all_sentences)
            from provenance import seal, sources
            # Only explicitly safe fixture sentences are certified. LEAK
            # assertions must not inherit a previously published receipt.
            plan["summary"] = good + " " + " ".join(s for s in all_sentences if "LEAK" not in s)
            seal(plan, sources({"idea": raw["summary"]}))
            # Both PDF types actually render these fields; bypass /generate to
            # exercise the export boundary independently, including old plans.
            plan["summary"] = body
            plan["first_step_today"] = body
            plan["readiness_report"]["main_risk"] = body
            for endpoint, payload in [
                ("/pdf", dict(plan, _lang=lang)),
                ("/investment/pdf", {"plan": plan, "finance": {"inputs": BASE}, "notes": {}, "lang": lang}),
            ]:
                with self.subTest(lang=lang, endpoint=endpoint):
                    response = app.app.test_client().post(endpoint, json=payload)
                    self.assertEqual(response.status_code, 200)
                    text = " ".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(response.data)).pages)
                    for marker, kind in markers.items():
                        self.assertEqual(marker in text, kind == "safe", (lang, endpoint, marker, kind))
                    response.close()
