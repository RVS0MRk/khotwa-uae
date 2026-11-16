"""Isolated local UI fixture server. Never calls Groq or reads a real key."""

import json
import os

from test_support import configure_mock_environment

configure_mock_environment()
import app as startsmart

DIRTY_ADVISOR = {
    "title": "### Test customer demand first",
    "summary": "No new evidence.",
    "points": [{"title": "**Demand:&#x20;**", "text": "&#x49;nterview five potential customers."}],
    "next_action": "**Next action:&#x20;**&#x52;ecord interviews.",
    "caution": "**Caution:&#x20;**&#x52;egulatory requirements are unverified.",
}


def fake_groq(system, user, **kwargs):
    from flask import request, has_request_context
    from pathlib import Path
    fixture = request.headers.get("X-Khotwa-Test-Fixture", "") if has_request_context() else ""
    if fixture == "ar-advisor" and "Founder Advisor" in system:
        return json.dumps({"title":"تحديث دليل الأدلة","summary":"لم أتمكن من إعداد إجابة موثوقة الآن.","points":[{"title":"سجّل الردود","text":"أدخل القيم في proof_mode_recorded_evidence_only لتتبع إجمالي الردود."}],"next_action":"اسأل عشرة مالكي سيارات في دبي.","caution":""},ensure_ascii=False)
    if fixture in ("live-lunch", "live-lunch-ar", "live-packaging", "adverse-lunch") and "Founder Advisor" not in system and "Suggest exactly three" not in system:
        name = "v224_live_lunch_ar" if fixture == "live-lunch-ar" else "v224_live_packaging" if fixture == "live-packaging" else "v224_live_lunch"
        raw = json.loads((Path(__file__).parent / "tests/fixtures" / (name + ".json")).read_text(encoding="utf-8"))
        if fixture == "adverse-lunch":
            raw["summary"] = "We closed a pre-seed round of AED 150,000."
            raw["pitches"] = {k: raw["summary"] for k in raw["pitches"]}
        return json.dumps(raw,ensure_ascii=False)
    if os.environ.get("V22_RICH") == "1" and "Suggest exactly three" not in system and "Founder Advisor" not in system:
        from pathlib import Path

        arabic = "Write ALL text values in Arabic" in system
        name = "rich_plan_ar" if arabic else "rich_plan_alt_en" if "coding" in user.lower() else "rich_plan_en"
        text = (Path(__file__).parent / "tests/fixtures" / f"{name}.json").read_text(encoding="utf-8")
        if fixture == "consistent-assessment" and arabic:
            raw = json.loads(text)
            for key in ("local_fit", "clear_customer", "low_starting_cost", "easy_first_step", "growth_potential"):
                raw["opportunity_score"][key]["reason"] = "قد تلائم الفكرة شريحة موظفي المكاتب؛ اختبر ملاءمتها قبل الإنفاق."
            return json.dumps(raw, ensure_ascii=False)
        return text
    if "Suggest exactly three" in system:
        ar = "Write all field values except category in Arabic" in system
        names = (
            ("خدمة غسيل سيارات متنقلة", "أداة تذكير بمواعيد السيارة", "خدمة بحث في ملحقات السيارات")
            if ar
            else ("Mobile car wash", "Vehicle reminder tool", "Car accessory research service")
        )
        return json.dumps(
            {
                "ideas": [
                    {
                        "name": name,
                        "fit": (
                            "توظف مهارات التصميم والتواصل"
                            if ar
                            else "Uses AutoCAD, communication and engineering skills"
                        ),
                        "customer": "مالكو السيارات" if ar else "Car owners",
                        "first_test": "مقابلات بلا دفع" if ar else "Offer free washes",
                        "assumption": "الحاجة إلى اختبار" if ar else "Strong demand",
                        "category": "Services & Maintenance",
                    }
                    for name in names
                ]
            },
            ensure_ascii=False,
        )
    if "Founder Advisor" in system:
        if "malformed" in user:
            return "```broken JSON {"
        return json.dumps(DIRTY_ADVISOR)
    if "malformed" in user:
        return "broken model response"
    ar = "Write ALL text values in Arabic" in system
    if "Ergonomic" in user:
        return json.dumps(
            {
                "business_name_suggestion": "Mobile Car‑Interior Ergonomic Consulting",
                "summary": "Interview ride‑hailing drivers face‑to‑face about perceived comfort.",
                "readiness_report": {"target_customer": "Daily commuters", "estimated_first_test_cost_aed": 200},
                "idea_overview": {"impact": "Lower injury risk, higher productivity and improves safety"},
                "total_estimated_cost_aed": 5000,
                "opportunity_score": {"total": 19},
            }
        )
    return json.dumps(
        {
            "business_name_suggestion": "اختبار خدمة غسيل السيارات" if ar else "Car wash validation",
            "summary": "Initial interviews suggest strong demand.",
            "readiness_report": {
                "target_customer": "مالكو السيارات السكنية" if ar else "Residential car owners",
                "estimated_first_test_cost_aed": 200,
                "main_risk": "mobile water-use permits",
            },
            "suggested_test_price_aed": 30,
            "total_estimated_cost_aed": 5000,
            "opportunity_score": {"total": 19},
            "steps": [
                {
                    "step_number": i + 1,
                    "action": "Validation step",
                    "description": "Test a planning assumption",
                    "estimated_cost_aed": cost,
                }
                for i, cost in enumerate([0, 0, 0, 0, 2000, 3000, 0])
            ],
            "pitches": {"ten_sec": "Proven water savings for just AED 30"},
        }
    )


if __name__ == "__main__":
    if os.environ.get("V22_RICH") == "1":
        from flask import send_file
        from pathlib import Path

        @startsmart.app.get("/__test/axe.js")
        def axe_asset():
            return send_file(
                Path(__file__).parent / "node_modules/axe-core/axe.min.js", mimetype="application/javascript"
            )

    startsmart.call_groq = fake_groq
    startsmart.app.run(host="127.0.0.1", port=int(os.environ.get("TEST_PORT", "5001")), debug=False)
