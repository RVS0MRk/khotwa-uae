"""Shared allowed input values and export-only display normalization."""
from decimal import Decimal, InvalidOperation
import math

REGIONS = {"UAE-wide", "Abu Dhabi", "Al Ain", "Dubai", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain", "Other UAE"}
CONTEXTS = {"Not sure", "Online", "Local service", "Local service or digital", "Retail", "Food & beverage", "Tourism", "B2B", "Campus", "Residential", "Rural", "Other"}
CATEGORIES = {"Food & Catering", "Agriculture & Farming", "Retail & Trading", "Tourism & Hospitality", "Services & Maintenance", "Technology & Digital", "Handicrafts & Arts", "Health & Wellness", "Education & Tutoring", "Services", "Other"}
USER_TYPES = {"", "students", "families", "tourists", "professionals", "small_businesses", "residents", "online_customers"}

# These are the app's Arabic display labels, not arbitrary translated prose.
ARABIC = {
    "category": {"الطعام والتموين", "الزراعة", "التجارة والبيع", "السياحة والضيافة", "الخدمات والصيانة", "التقنية والرقمية", "الحرف والفنون", "الصحة", "التعليم", "الخدمات", "أخرى"},
    "region": {"كل الإمارات / غير متأكد", "الإمارات", "كل الإمارات", "أبوظبي", "العين", "دبي", "الشارقة", "عجمان", "رأس الخيمة", "الفجيرة", "أم القيوين", "منطقة أخرى في الإمارات"},
    "context": {"غير متأكد", "أونلاين / رقمي", "خدمة محلية", "خدمة محلية أو رقمية", "تجزئة / متجر", "طعام ومشروبات", "سياحة / ضيافة", "أعمال لشركات", "جامعة / طلاب", "سكني / عائلات", "ريفي / زراعي", "أخرى"},
    "user_type": {"أي / غير متأكد", "الطلاب", "العائلات / الأسر", "السياح / الزوار", "المهنيون", "المشاريع الصغيرة", "السكان", "عملاء أونلاين"},
}
CHOICES = {"category": CATEGORIES, "region": REGIONS, "context": CONTEXTS, "user_type": USER_TYPES}
DEFAULTS = {"category": "Other", "region": "UAE-wide", "context": "Not sure", "user_type": ""}
RISK = {"High": "High", "Medium": "Medium", "Low": "Low", "مرتفع": "High", "مرتفعة": "High", "عالي": "High", "عال": "High", "متوسط": "Medium", "متوسطة": "Medium", "منخفض": "Low", "منخفضة": "Low"}


def display_value(value, kind):
    if isinstance(value, str) and value in CHOICES[kind] | ARABIC[kind]:
        return value
    return DEFAULTS[kind]


def budget_value(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        return 0
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number < 0:
            return 0
        result = float(number)
        return result if math.isfinite(result) else 0
    except (InvalidOperation, ValueError, OverflowError):
        return 0


def sanitize_export_display(plan):
    """Enums/budget cannot be used as unsigned narrative sinks.

    This changes only display aliases, never the signature/ledger, financial
    inputs, Proof observations or the labelled founder's state.idea.
    """
    state = plan.get("state")
    if not isinstance(state, dict):
        state = plan["state"] = {}
    for kind in CHOICES:
        state_key = "customer_type" if kind == "user_type" else kind
        for owner, key in ((state, state_key), (plan, "_" + kind), (plan, kind)):
            if key in owner:
                owner[key] = display_value(owner[key], kind)
    for owner, key in ((state, "user_budget_aed"), (plan, "_budget"), (plan, "budget")):
        if key in owner:
            owner[key] = budget_value(owner[key])
    for risk in plan.get("risk_radar", []) or []:
        if isinstance(risk, dict):
            risk["level"] = RISK.get(risk.get("level"), "Medium") if isinstance(risk.get("level"), str) else "Medium"
    decision = plan.get("decision_engine")
    if isinstance(decision, dict) and "risk_level" in decision:
        value = decision["risk_level"]
        decision["risk_level"] = RISK.get(value, "Medium") if isinstance(value, str) else "Medium"
    return plan
