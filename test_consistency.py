"""Dashboard/Founder assessment contract. Provider access is forbidden."""
import io
import json
import unittest
from copy import deepcopy
from unittest.mock import patch

from test_support import configure_mock_environment
configure_mock_environment()
import app
from content_safety import export_plan
from provenance import seal, sources, verified_receipt
from scoring import DIMENSIONS, proof_counts, proof_evidence_text
from test_v22_content import fixture


def observations(total=5, **changes):
    return dict(total_responses=total, interested=total, **changes)


class FounderConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.network = patch("requests.post", side_effect=AssertionError("No live requests permitted"))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.client = app.app.test_client()

    def generate(self, lang="en"):
        raw = fixture("rich_plan_" + lang)
        if lang == "ar":
            for key in DIMENSIONS:
                raw["opportunity_score"][key]["reason"] = "قد تلائم الفكرة شريحة موظفي المكاتب؛ اختبر ملاءمتها قبل الإنفاق."
        with patch.object(app, "call_groq", return_value=json.dumps(raw, ensure_ascii=False)):
            response = self.client.post("/generate", json={"idea": "Lunch boxes for office workers", "budget": 6500,
                                                          "region": "Abu Dhabi", "lang": lang})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["opportunity_score"]["total"], 15)
        return response.json

    def test_generated_receipt_authenticates_original_assessment(self):
        plan = self.generate()
        receipt = verified_receipt(plan)
        self.assertEqual(receipt["version"], 3)
        self.assertEqual(receipt["assessment"], plan["opportunity_score"])
        self.assertEqual(receipt["canonical_id"], plan["_canonical_id"])

    def test_zero_five_changed_and_cleared_match_current_assessment(self):
        plan = self.generate()
        for proof, expected in [(None, 15), (observations(), 15),
                                (observations(actual_payments=1), 18),
                                (observations(no_payment_reservations=1), 17),
                                (observations(stated_intent=1), 16), (None, 15)]:
            with self.subTest(proof=proof):
                if proof is None:
                    plan.pop("proof_summary", None)
                else:
                    plan["proof_summary"] = proof
                # Never trust posted score, reason or browser backup.
                plan["opportunity_score"]["total"] = 25
                plan["opportunity_score"]["clear_customer"] = {"score": 5, "reason": "Untrusted posted explanation"}
                plan["opportunity_score"]["_before_evidence"] = {"score": 5, "reason": "Untrusted old backup"}
                clean = export_plan(plan)
                self.assertEqual(clean["opportunity_score"]["total"], expected)
                self.assertEqual(clean["opportunity_score"]["status"], "provisional")
                self.assertEqual(clean["state"]["opportunity_score"], clean["opportunity_score"])
                self.assertEqual(clean["idea_overview"]["evidence"], proof_evidence_text(proof_counts(proof)))
                if proof:
                    self.assertEqual(clean["opportunity_score"]["clear_customer"]["source"], "recorded_evidence")
                    self.assertIn("not independently verified", clean["decision_engine"]["reason"].lower())
                else:
                    self.assertEqual(clean["decision_engine"], verified_receipt(plan)["decision"])

    def test_under_five_entries_does_not_change_score(self):
        plan = self.generate()
        plan["proof_summary"] = observations(4, actual_payments=1)
        clean = export_plan(plan)
        self.assertEqual(clean["opportunity_score"]["total"], 15)
        self.assertIn("4 self-reported", clean["idea_overview"]["evidence"])

    def test_proof_rule_matches_browser_for_complete_partial_and_missing_bases(self):
        from pathlib import Path
        import subprocess
        from scoring import normalize_scores, assessment_from_proof
        cases = []
        for lang in ("en", "ar"):
            for missing in (0, 1, 5):
                raw = {key: {"score": i + 1, "reason": "A planning assumption that needs a customer test."}
                       for i, key in enumerate(DIMENSIONS) if i >= missing}
                baseline = normalize_scores(raw, lang=lang)
                for proof in ({}, observations(4, actual_payments=1), observations(),
                              observations(actual_payments=1), observations(repeat_customers=1),
                              observations(stated_intent=1), observations(no_payment_reservations=1)):
                    counts = proof_counts(proof)
                    cases.append({"lang": lang, "score": baseline, "counts": counts,
                                  "expected": assessment_from_proof(baseline, counts, lang)})
        script = """
const fs=require('fs'),vm=require('vm');const cases=JSON.parse(fs.readFileSync(0,'utf8'));
const code=fs.readFileSync('static/scoring.js','utf8');
const result=cases.map(r=>{const c={lang:r.lang,currentPlan:{opportunity_score:r.score}};vm.createContext(c);vm.runInContext(code,c);
const p=r.counts;c.updateEvidenceScore(p.total_responses,p.interested,p.stated_intent,p.no_payment_reservations,p.actual_payments,p.repeat_customers);
delete c.currentPlan.opportunity_score._before_evidence;return c.currentPlan.opportunity_score;});process.stdout.write(JSON.stringify(result));
"""
        result = subprocess.run(["node", "-e", script], input=json.dumps(cases), encoding="utf-8", capture_output=True,
                                check=True, cwd=Path(__file__).parent)
        self.assertEqual(json.loads(result.stdout), [case["expected"] for case in cases])

    def test_bad_signatures_identity_ledger_and_receipt_numbers_fail_closed(self):
        original = self.generate()
        for mutation in ("signature", "identity", "ledger", "assessment", "absent"):
            with self.subTest(mutation=mutation):
                plan = deepcopy(original)
                if mutation == "signature": plan["_content_receipt"]["signature"] = "forged"
                elif mutation == "identity": plan["_canonical_id"] = "different-plan"
                elif mutation == "ledger": plan["_provenance"]["external_achievement_evidence"] = ["invented"]
                elif mutation == "assessment": plan["_content_receipt"]["assessment"]["local_fit"]["score"] = 5
                else: plan.pop("_content_receipt")
                plan["proof_summary"] = observations(actual_payments=1)
                clean = export_plan(plan)
                self.assertIsNone(verified_receipt(plan))
                self.assertIsNone(clean["opportunity_score"]["total"])
                self.assertEqual(clean["opportunity_score"]["assessed_count"], 1)
                self.assertEqual(clean["opportunity_score"]["status"], "incomplete")

    def test_incomplete_baseline_does_not_invent_missing_dimensions(self):
        plan = self.generate()
        plan["opportunity_score"]["local_fit"] = {}
        seal(plan, sources({}, plan))
        plan["proof_summary"] = observations(actual_payments=1)
        clean = export_plan(plan)
        self.assertIsNone(clean["opportunity_score"]["total"])
        self.assertEqual(clean["opportunity_score"]["assessed_count"], 4)

    def test_invalid_counts_do_not_boost_or_display_false_observations(self):
        plan = self.generate()
        for proof in ([1], "5", {"total_responses": True}, {"total_responses": 11},
                      {"total_responses": 5, "actual_payments": 6},
                      {"total_responses": 5, "interested": 5, "no": 1},
                      {"total_responses": 5, "actual_payments": 3, "repeat_customers": 3},
                      {"total_responses": "5"}, {"total_responses": -1}):
            with self.subTest(proof=proof):
                self.assertIsNone(proof_counts(proof))
                plan["proof_summary"] = proof
                clean = export_plan(plan)
                self.assertEqual(clean["opportunity_score"]["total"], 15)
                self.assertEqual(clean["proof_summary"], {})
                self.assertFalse(clean["_proof_presentation"]["valid_counts"])

    def test_edited_prose_is_still_filtered_with_valid_proof(self):
        plan = self.generate()
        plan["summary"] = "We secured AED 150,000 funding and confirmed a successful launch."
        plan["proof_summary"] = observations(actual_payments=1)
        clean = export_plan(plan)
        self.assertEqual(clean["summary"], "")
        self.assertEqual(clean["opportunity_score"]["total"], 18)
        self.assertFalse(clean["_current_sources"]["entries"]["proof"]["verified"])
        self.assertEqual(clean["_current_sources"]["external_achievement_evidence"], [])

    def test_export_language_controls_only_application_copy(self):
        plan = self.generate()
        original = plan["summary"]
        plan["proof_summary"] = observations(actual_payments=1)
        plan["_export_lang"] = "ar"
        clean = export_plan(plan)
        self.assertIn("بإقرار المستخدم", clean["idea_overview"]["evidence"])
        self.assertEqual(clean["summary"], original)
        self.assertEqual(clean["opportunity_score"]["total"], 18)

    def test_legacy_receipt_preserves_prose_without_authenticating_numbers(self):
        import hashlib
        import hmac
        import provenance
        plan = self.generate()
        payload = {k: plan["_content_receipt"][k] for k in ("strings", "ledger_hash")}
        payload["version"] = 2
        with patch.object(provenance, "_SIGNING_KEY", b"test-only-receipt-key"):
            signature = hmac.new(b"test-only-receipt-key", provenance.digest(payload).encode(), hashlib.sha256).hexdigest()
            plan["_content_receipt"] = dict(payload, signature=signature)
            clean = export_plan(plan)
            self.assertEqual(clean["summary"], plan["summary"])
            self.assertIsNone(clean["opportunity_score"]["total"])

    def test_incomplete_or_tampered_assessment_stays_incomplete_in_actual_pdf(self):
        from pypdf import PdfReader
        import unicodedata
        for mutation in ("missing_dimension", "bad_signature", "changed_identity"):
            plan = self.generate()
            if mutation == "missing_dimension":
                plan["opportunity_score"]["local_fit"] = {}
                seal(plan, sources({}, plan))
            elif mutation == "bad_signature":
                plan["_content_receipt"]["signature"] = "forged"
            else:
                plan["_canonical_id"] = "different-business"
            if mutation != "changed_identity":
                plan.pop("_alternate_plan", None)
            plan["proof_summary"] = observations(actual_payments=1)
            for lang in ("en", "ar"):
                with self.subTest(mutation=mutation, lang=lang):
                    response = self.client.post("/pdf", json=dict(plan, _lang=lang))
                    self.assertEqual(response.status_code, 200)
                    first = unicodedata.normalize("NFKC", PdfReader(io.BytesIO(response.data)).pages[0].extract_text())
                    self.assertIn("غير مكتمل" if lang == "ar" else "Incomplete", first)
                    self.assertNotRegex(first, r"(?:18|25)\s*/\s*25")
                    response.close()

    def test_founder_pdf_bilingual_actual_content_for_all_four_states(self):
        from pypdf import PdfReader
        from founder_pdf import shape_ar
        import re
        import unicodedata
        def compact(text):
            return re.sub(r"\s+", "", "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)))
        for native in ("en", "ar"):
            plan = self.generate(native)
            for name, proof, expected in (("none", None, 15), ("five", observations(), 15),
                                          ("changed", observations(actual_payments=1), 18), ("clear", None, 15)):
                plan["proof_summary"] = proof or {}
                for lang in ("en", "ar"):
                    with self.subTest(native=native, state=name, export=lang):
                        response = self.client.post("/pdf", json=dict(plan, _lang=lang))
                        self.assertEqual(response.status_code, 200)
                        pages = PdfReader(io.BytesIO(response.data)).pages
                        first = pages[0].extract_text()
                        text = "\n".join(p.extract_text() for p in pages)
                        self.assertRegex(first, rf"{expected}\s*/\s*25")
                        self.assertNotIn("Incomplete", first)
                        self.assertNotIn(compact(shape_ar("غير مكتمل")), compact(first))
                        if lang == "en":
                            self.assertIn(proof_evidence_text(proof_counts(proof)), text)
                            self.assertIn(proof_evidence_text(proof_counts(proof)), first)
                            self.assertIn("Provisional assessment", first)
                            if proof:
                                self.assertIn(compact("Review pilot evidence" if name == "changed" else "Validate more"), compact(first))
                            if proof: self.assertNotIn("No customer feedback entered yet", text)
                        else:
                            # Whole narrative may wrap; verify shaped distinctive words.
                            for word in (("إجابات", "بإقرار", "مستقل") if proof else ("تُسجّل", "ملاحظات")):
                                self.assertTrue(compact(word) in compact(text) or compact(shape_ar(word)) in compact(text), word)
                        response.close()


if __name__ == "__main__":
    unittest.main()
