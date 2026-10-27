"""Isolated local UI fixture server. Never calls Groq or reads a real key."""
import json
import os

os.environ["GROQ_API_KEY"] = "test-only-placeholder"
import app as startsmart

DIRTY_ADVISOR = {
    "title": "### Test customer demand first",
    "summary": "No new evidence.",
    "points": [{"title": "**Demand:&#x20;**", "text": "&#x49;nterview five potential customers."}],
    "next_action": "**Next action:&#x20;**&#x52;ecord interviews.",
    "caution": "**Caution:&#x20;**&#x52;egulatory requirements are unverified."
}

def fake_groq(system, user, **kwargs):
    if "Suggest exactly three" in system:
        return json.dumps({"ideas": [
            {"name": name, "fit": "Uses AutoCAD, communication and engineering skills", "customer": "Car owners",
             "first_test": "Offer free washes", "assumption": "Strong demand", "category": "Services & Maintenance"}
            for name in ("Mobile car wash", "Vehicle reminder tool", "Car accessory research service")
        ]})
    if "Founder Advisor" in system:
        if "malformed" in user:
            return "```broken JSON {"
        return json.dumps(DIRTY_ADVISOR)
    if "malformed" in user:
        return "broken model response"
    ar = "Write ALL text values in Arabic" in system
    if "Ergonomic" in user:
        return json.dumps({"business_name_suggestion": "Mobile Car‑Interior Ergonomic Consulting",
            "summary": "Interview ride‑hailing drivers face‑to‑face about perceived comfort.",
            "readiness_report": {"target_customer": "Daily commuters", "estimated_first_test_cost_aed": 200},
            "idea_overview": {"impact": "Lower injury risk, higher productivity and improves safety"},
            "total_estimated_cost_aed": 5000, "opportunity_score": {"total": 19}})
    return json.dumps({"business_name_suggestion": "اختبار خدمة غسيل السيارات" if ar else "Car wash validation",
        "summary": "Initial interviews suggest strong demand.",
        "readiness_report": {"target_customer": "مالكو السيارات السكنية" if ar else "Residential car owners", "estimated_first_test_cost_aed": 200,
                             "main_risk": "mobile water-use permits"},
        "suggested_test_price_aed": 30, "total_estimated_cost_aed": 5000,
        "opportunity_score": {"total": 19},
        "steps": [{"step_number": i+1, "action": "Validation step", "description": "Test a planning assumption", "estimated_cost_aed": cost} for i, cost in enumerate([0, 0, 0, 0, 2000, 3000, 0])],
        "pitches": {"ten_sec": "Proven water savings for just AED 30"}})


if __name__ == "__main__":
    startsmart.call_groq = fake_groq
    startsmart.app.run(host="127.0.0.1", port=int(os.environ.get("TEST_PORT", "5001")), debug=False)
