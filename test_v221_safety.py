"""Independent table-driven success-claim and export-boundary regressions."""

import io
import json
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from test_support import configure_mock_environment

configure_mock_environment()
import app
from content_safety import safe_text, export_plan, offending
from test_v22_content import fixture, strings

CASES = json.loads((Path(__file__).parent / "tests/fixtures/v221_safety.json").read_text(encoding="utf-8"))


def leaves(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, path + (key,))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from leaves(child, path + (i,))
    elif isinstance(value, str):
        yield path, value


def at(value, path):
    for part in path:
        value = value[part]
    return value


class V221SafetyTests(unittest.TestCase):
    def setUp(self):
        transport = patch("requests.post", side_effect=AssertionError("Live transport forbidden in safety tests"))
        transport.start()
        self.addCleanup(transport.stop)

    def test_independent_unsafe_and_legitimate_language_tables(self):
        for lang in ("en", "ar"):
            for kind in ("unsafe", "safe"):
                for text in CASES[kind + "_" + lang]:
                    with self.subTest(lang=lang, kind=kind, text=text):
                        self.assertEqual(safe_text(text, lang), text if kind == "safe" else "")

    def test_separate_sentence_or_clause_cannot_borrow_negation_or_condition(self):
        for lang in ("en", "ar"):
            good = (
                "Interview office workers about lunch choices."
                if lang == "en"
                else "اسأل موظفي المكاتب عن خيارات الغداء."
            )
            condition = (
                "If interviews confirm demand, test a proposed lunch subscription."
                if lang == "en"
                else "إذا أكدت المقابلات الطلب فقد تكون الفكرة مجدية."
            )
            for bad in CASES["unsafe_" + lang]:
                with self.subTest(lang=lang, bad=bad):
                    self.assertEqual(safe_text(f"{condition} {bad} {good}", lang), f"{condition} {good}")
                    self.assertTrue(
                        offending(f"{condition} {bad}"), "Direct cost guards must not borrow a previous condition"
                    )

    def test_three_claims_across_every_model_string_leaf(self):
        # All raw fields, not just the six reported leaks. Metadata is asserted
        # too: it must be replaced by authoritative schema labels, never leaked.
        for lang in ("en", "ar"):
            raw = fixture("rich_plan_" + lang)
            inputs = {"idea": raw["summary"], "budget": 5000, "region": "Abu Dhabi"}
            clean = app._normalize_plan(raw, inputs, lang)
            for path, good in leaves(raw):
                for bad in CASES["unsafe_" + lang][:3]:
                    with self.subTest(lang=lang, field=path, bad=bad):
                        dirty = deepcopy(raw)
                        at(dirty, path[:-1])[path[-1]] = good.rstrip(".!?؟") + ". " + bad
                        result = app._normalize_plan(dirty, inputs, lang)
                        self.assertFalse(bad in json.dumps(result, ensure_ascii=False), f"Claim leaked at {path}")
                        # Where this field is retained in the clean baseline,
                        # it must still retain its original specific sentence.
                        try:
                            baseline = at(clean, path)
                            actual = at(result, path)
                        except (KeyError, IndexError, TypeError):
                            continue
                        if (
                            baseline == good
                            and path[-1] not in ("level", "name", "decision", "status", "source")
                            and len(good.split()) + len(bad.split()) <= 25
                        ):
                            self.assertTrue(actual.startswith(good.rstrip(".!?؟")), (path, actual, good))

    def test_advisor_all_fields_and_discovery_all_fields(self):
        for lang in ("en", "ar"):
            good = (
                "Interview office workers about lunch choices."
                if lang == "en"
                else "اسأل موظفي المكاتب عن خيارات الغداء."
            )
            for bad in CASES["unsafe_" + lang]:
                text = f"{good} {bad}"
                answer = {
                    "title": text,
                    "summary": text,
                    "points": [{"title": text, "text": text}],
                    "next_action": text,
                    "caution": text,
                }
                with self.subTest(lang=lang, bad=bad):
                    with patch.object(app, "call_groq", return_value=json.dumps(answer)):
                        r = app.app.test_client().post("/ask", json={"question": "Suggest a next test", "lang": lang})
                    self.assertEqual(r.status_code, 200)
                    self.assertEqual(list(strings(r.json["answer"])), [good] * 6)
            bad = " ".join(CASES["unsafe_" + lang][:3])
            card = {k: f"{good} {bad}" for k in ("name", "fit", "customer", "first_test", "assumption")}
            card["category"] = "Food & Catering"
            with patch.object(app, "call_groq", return_value=json.dumps({"ideas": [card] * 3})):
                r = app.app.test_client().post("/discover", json={"skills": "Cooking", "budget": 1000, "lang": lang})
            self.assertEqual(r.status_code, 200)
            for bad in CASES["unsafe_" + lang][:3]:
                self.assertNotIn(bad, json.dumps(r.json, ensure_ascii=False))
            self.assertIn(good, json.dumps(r.json, ensure_ascii=False))

    def test_export_boundary_preserves_user_records_but_rechecks_model_prose(self):
        for lang in ("en", "ar"):
            raw = fixture("rich_plan_" + lang)
            bad = " ".join(CASES["unsafe_" + lang][:3])
            for path, good in list(leaves(raw)):
                at(raw, path[:-1])[path[-1]] = good + " " + bad
            raw["state"] = {
                "idea": "The founder's original concept",
                "target_customer": "Office workers. " + bad,
                "evidence": {"total_responses": 2},
            }
            raw["readiness_report"]["idea"] = raw["state"]["idea"]
            raw["proof_summary"] = {"total_responses": 2, "actual_payments": 1, "demo": False}
            raw["_financial_inputs"] = {"price": "0", "units": "10"}
            clean = export_plan(raw)
            for claim in CASES["unsafe_" + lang][:3]:
                self.assertNotIn(claim, json.dumps(clean, ensure_ascii=False))
            for key in ("proof_summary", "_financial_inputs"):
                self.assertEqual(clean[key], raw[key])
            self.assertEqual(clean["state"]["idea"], raw["state"]["idea"])
            self.assertEqual(clean["state"]["evidence"], raw["state"]["evidence"])
            self.assertNotEqual(raw, clean, "Caller-owned plan must not be mutated")

    def test_generated_plans_cannot_turn_model_traction_or_score_into_evidence(self):
        for lang in ("en", "ar"):
            raw = fixture("rich_plan_" + lang)
            raw["proof_summary"] = {"total_responses": 40, "actual_payments": 40}
            raw["state"] = {"evidence": {"total_responses": 40}}
            raw["summary"] += " " + " ".join(CASES["unsafe_" + lang][:3])
            with patch.object(app, "call_groq", return_value=json.dumps(raw)):
                response = app.app.test_client().post("/generate", json={"idea": "Lunch boxes", "lang": lang})
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("proof_summary", response.json)
            self.assertNotEqual((response.json.get("state", {}).get("evidence") or {}).get("total_responses"), 40)
            for bad in CASES["unsafe_" + lang][:3]:
                self.assertNotIn(bad, json.dumps(response.json, ensure_ascii=False))

    def test_english_pdf_bytes_do_not_reintroduce_success_claims(self):
        from pypdf import PdfReader
        from test_finance import BASE

        raw = fixture()
        plan = app._normalize_plan(raw, {"idea": raw["summary"], "budget": 5000}, "en")
        for path, text in list(leaves(plan)):
            if (
                path[0] not in ("state", "proof_summary")
                and path != ("readiness_report", "idea")
                and not str(path[0]).startswith("_")
            ):
                at(plan, path[:-1])[path[-1]] = text + " " + " ".join(CASES["unsafe_en"][:3])
        for endpoint, payload in (
            ("/pdf", dict(plan, _lang="en")),
            ("/investment/pdf", {"plan": plan, "finance": {"inputs": BASE}, "notes": {}, "lang": "en"}),
        ):
            with self.subTest(endpoint=endpoint):
                response = app.app.test_client().post(endpoint, json=payload)
                self.assertEqual(response.status_code, 200)
                text = " ".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(response.data)).pages)
                for bad in CASES["unsafe_en"][:3]:
                    self.assertNotIn(bad, text)
                self.assertIn("office workers", text.lower())
                response.close()

    def test_arabic_exporters_use_clean_plan_before_shaping_and_keep_user_notes(self):
        import founder_pdf
        import financial_report
        from test_finance import BASE

        raw = fixture("rich_plan_ar")
        plan = app._normalize_plan(raw, {"idea": raw["summary"], "budget": 5000}, "ar")
        claims = " ".join(CASES["unsafe_ar"][:3])
        for path in (
            ("summary",),
            ("idea_overview", "problem"),
            ("idea_overview", "solution"),
            ("readiness_report", "main_risk"),
            ("first_step_today",),
            ("pitches", "whatsapp"),
        ):
            at(plan, path[:-1])[path[-1]] += " " + claims
        notes = {"model": "اشتراك أسبوعي مقترح لصناديق الغداء"}
        for endpoint, payload, module in (
            ("/pdf", dict(plan, _lang="ar"), founder_pdf),
            (
                "/investment/pdf",
                {"plan": plan, "finance": {"inputs": BASE}, "notes": notes, "lang": "ar"},
                financial_report,
            ),
        ):
            with self.subTest(endpoint=endpoint), patch.object(module, "export_plan", wraps=export_plan) as boundary:
                response = app.app.test_client().post(endpoint, json=payload)
                self.assertEqual(response.status_code, 200)
                boundary.assert_called_once()
                cleaned = export_plan(boundary.call_args.args[0])
                for bad in CASES["unsafe_ar"][:3]:
                    self.assertNotIn(bad, json.dumps(cleaned, ensure_ascii=False))
                self.assertIn(raw["idea_overview"]["solution"], json.dumps(cleaned, ensure_ascii=False))
                self.assertEqual(notes["model"], payload.get("notes", notes)["model"])
                response.close()
