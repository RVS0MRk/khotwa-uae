"""Small release-hardening regressions; all provider transport forbidden."""

import io
import json
import re
import hashlib
import unicodedata
import unittest
from pathlib import Path
from collections import Counter
from unittest.mock import patch

from test_support import configure_mock_environment

configure_mock_environment()
import app
import content_safety
from content_safety import safe_text
from disclosures import AI_DISCLOSURE, PROOF_DISCLOSURE
from test_v22_content import fixture, normalized, strings
from test_v222_safety import FIELDS
from test_v221_safety import at

ROOT = Path(__file__).parent
PRECISION = [
    "Pre-ordered healthy lunch boxes delivered to office workers in Abu Dhabi.",
    "None of the 10 people you interviewed has paid yet.",
]


def pdf_words(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u064b-\u065f\u0670\u0640]", "", text)
    return " ".join(text.split())


class V223Tests(unittest.TestCase):
    def setUp(self):
        transport = patch("requests.post", side_effect=AssertionError("Live provider forbidden"))
        transport.start()
        self.addCleanup(transport.stop)

    def test_precision_in_five_fields_and_advisor(self):
        for sentence in PRECISION:
            self.assertEqual(safe_text(sentence), sentence)
            for path in FIELDS:
                raw = fixture()
                at(raw, path[:-1])[path[-1]] = sentence
                plan = app._normalize_plan(raw, {"idea": "Lunch boxes", "budget": 5000}, "en")
                self.assertEqual(at(plan, path), sentence)
            answer = {
                "title": "Lunch planning",
                "summary": sentence,
                "points": [{"title": "Next test", "text": sentence}],
                "next_action": sentence,
                "caution": "",
            }
            with patch.object(app, "call_groq", return_value=json.dumps(answer)):
                r = app.app.test_client().post("/ask", json={"question": "What should I test?", "lang": "en"})
            self.assertEqual(r.status_code, 200)
            for value in [
                r.json["answer"]["summary"],
                r.json["answer"]["points"][0]["text"],
                r.json["answer"]["next_action"],
            ]:
                self.assertEqual(value, sentence)

    def test_morphology_and_negation_only_change_matching_copy(self):
        for text in (
            "خدمتنا مربحة منذ الشهر الأول.",
            "صار مطعمنا مربحًا.",
            "خدمتها مربحة.",
            "خدمتهم مربحة.",
            "خدمتك مربحة.",
        ):
            self.assertEqual(safe_text(text, "ar"), "")
        for text in (
            "خدمتنا ليست مربحة بعد.",
            "قد تصبح خدمتنا مربحة إذا أكدت المقابلات الطلب.",
            "لم يدفع أي من الأشخاص العشرة الذين قابلتهم حتى الآن.",
        ):
            self.assertEqual(safe_text(text, "ar"), text)
        for text in (
            "Not one of the customers has paid yet.",
            "No one has paid yet.",
            "Nobody has paid yet.",
            "The customers have not actually paid yet.",
            "None of the customers paid yet.",
            "Not one of the clients is paying yet.",
            "Lunch boxes ordered online for office workers.",
        ):
            self.assertEqual(safe_text(text), text)
        for text in (
            "We sold 40 subscriptions yesterday.",
            "Customers have ordered 40 boxes.",
            "Booked 40 orders last month.",
            "Sold out every batch so far.",
            "Office teams ordered the complete meal batch.",
        ):
            self.assertEqual(safe_text(text), "")

    def test_existing_detector_vocabulary_patterns_are_unchanged(self):
        lock = json.loads((ROOT / "tests/fixtures/v223_pattern_lock.json").read_text(encoding="utf-8"))
        for name, digest in lock.items():
            self.assertEqual(hashlib.sha256(getattr(content_safety, name).pattern.encode()).hexdigest(), digest, name)

    def test_rich_retention_and_reviewer_summary(self):
        for name, lang in [("rich_plan_en", "en"), ("rich_plan_alt_en", "en"), ("rich_plan_ar", "ar")]:
            raw = fixture(name)
            if name == "rich_plan_en":
                raw["summary"] = PRECISION[0]
            result = app._normalize_plan(raw, {"idea": raw["summary"], "budget": 5000, "region": "Abu Dhabi"}, lang)
            before = list(strings(raw))
            after = set(strings(result))
            self.assertGreaterEqual(sum(s in after for s in before) / len(before), 0.86)
            if name == "rich_plan_en":
                self.assertEqual(result["summary"], PRECISION[0])

    def test_fixed_notices_and_precision_in_pdf_text(self):
        from pypdf import PdfReader
        from test_finance import BASE

        for lang in ("en", "ar"):
            plan = normalized("rich_plan_" + lang, lang)
            if lang == "en":
                plan["summary"] = PRECISION[0]
                plan["first_step_today"] = PRECISION[1]
                plan["idea_overview"]["problem"] = PRECISION[0]
            # Model/client text cannot override the application-owned notice.
            plan["ai_disclosure"] = "This business is independently verified."
            for endpoint, payload in [
                ("/pdf", dict(plan, _lang=lang)),
                ("/investment/pdf", {"plan": plan, "finance": {"inputs": BASE}, "notes": {}, "lang": lang}),
            ]:
                with self.subTest(lang=lang, endpoint=endpoint):
                    r = app.app.test_client().post(endpoint, json=payload)
                    self.assertEqual(r.status_code, 200)
                    pdf = PdfReader(io.BytesIO(r.data))
                    page = pdf_words(pdf.pages[0].extract_text())
                    if lang == "en":
                        for note in (AI_DISCLOSURE[lang], PROOF_DISCLOSURE[lang]):
                            self.assertIn(note, page)
                        all_text = pdf_words(" ".join(p.extract_text() or "" for p in pdf.pages))
                        for text in PRECISION:
                            self.assertIn(text, all_text)
                        if endpoint == "/pdf":
                            for label in ("Summary", "Problem", "Solution", "Why this market"):
                                self.assertIn(label + " (AI ASSUMPTION)", all_text)
                    else:
                        # Extraction unshapes Arabic but ReportLab line wraps can
                        # reorder words. Check every word in the disclosure block,
                        # before any business content, then visually inspect renders.
                        boundary = "اسم تجاري مقترح" if endpoint == "/pdf" else "فكرة المشروع"
                        self.assertIn(boundary, page)
                        prefix = page.split(boundary)[0]
                        for note in (AI_DISCLOSURE[lang], PROOF_DISCLOSURE[lang]):
                            self.assertIn(pdf_words(note), prefix)
                        expected = Counter(
                            re.findall(r"\w+", pdf_words(AI_DISCLOSURE[lang] + " " + PROOF_DISCLOSURE[lang]))
                        )
                        actual = Counter(re.findall(r"\w+", prefix))
                        self.assertFalse(expected - actual, expected - actual)
                    r.close()
