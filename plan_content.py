"""Validate useful model fields individually; templates only fill invalid slots."""

from copy import deepcopy
import re
import math
from content_safety import safe_text, MISSING, language_matches, offending
from scoring import normalize_scores, DIMENSIONS

PITCH_LIMITS = {"ten_sec": 25, "thirty_sec": 75, "whatsapp": 45, "instagram": 40}
DAY_THEMES = [
    r"customer|segment|define|عميل|شريحة|حد",
    r"interview|ask|conversation|مقابل|اسأل",
    r"offer|message|page|test|عرض|رسالة|صفحة|اختبر",
    r"intent|waitlist|reservation|نية|نوايا|حجز|انتظار",
    r"review|evidence|compare|راجع|أدلة|قارن",
    r"verify|check|requirements|تحقق|متطلبات|راجع",
    r"decide|decision|adjust|continue|قرر|قرار|عد",
]
STEP_THEMES = [DAY_THEMES[i] for i in (1, 3, 4, 5)] + [
    r"prepare|plan|جهز|خط",
    r"permitted|confirm|lawful|pilot|سمح|تأكيد|تجربة",
    DAY_THEMES[6],
]


def _trim_words(text, maximum):
    words = text.split()
    return text if len(words) <= maximum else " ".join(words[:maximum]).rstrip(".,;:؟!") + "."


def compose_pitches(plan, lang):
    state = plan.get("state") or {}
    idea = state.get("idea") or ""
    name = safe_text(plan.get("business_name_suggestion"), lang, minimum=3) or _trim_words(idea, 6)
    problem = (plan.get("idea_overview") or {}).get("problem") or ""
    if problem == MISSING[lang]:
        problem = "The customer problem still needs clarification." if lang == "en" else "تحتاج مشكلة العميل إلى توضيح."
    problem = problem.rstrip(".؟!") + ("." if lang == "en" else ".")
    target = state.get("target_customer") or ("potential customers" if lang == "en" else "عملاء محتملين")
    if lang == "ar":
        intro = f"{name}: {problem}"
        invitation = f"نختبر عرضاً بسيطاً مع {target} ونرحب برأيك الصريح دون بيع أو دفع."
        fallback = {
            "ten_sec": f"{name}: عرض مقترح نختبر فائدته مع العملاء قبل الإنفاق.",
            "thirty_sec": f"{intro} {invitation}",
            "whatsapp": f"مرحباً، {intro} {invitation}",
            "instagram": f"{intro} نبحث عن آراء حول البدائل الحالية دون بيع.",
        }
    else:
        intro = f"{name}: {problem}"
        invitation = f"We are testing a simple offer with {target} and would value your honest view."
        fallback = {
            "ten_sec": f"{name}: a proposed offer we are testing with potential customers before spending.",
            "thirty_sec": f"{intro} {invitation}",
            "whatsapp": f"Hi, {intro} {invitation}",
            "instagram": f"{intro} We would value honest feedback about current alternatives.",
        }
    price = state.get("suggested_test_price_aed")
    if isinstance(price, (int, float)) and price > 0:
        fallback["thirty_sec"] += (
            f" فرضية سعر للاختبار: {price:,.2f} AED؛ حدّد وحدة البيع ونطاقها."
            if lang == "ar"
            else f" Price hypothesis: AED {price:,.0f} (AI ASSUMPTION); define the unit and scope before testing."
        )
    current = plan.get("pitches") or {}
    plan["pitches"] = {
        k: _trim_words(safe_text(current.get(k), lang, fallback[k]), limit) for k, limit in PITCH_LIMITS.items()
    }
    return plan["pitches"]


def normalize_plan(raw, inputs, lang, template_factory, sync_costs):
    if not isinstance(raw, dict):
        raise ValueError("Invalid plan")
    original = deepcopy(raw)
    plan = template_factory(deepcopy(raw), inputs, lang)
    idea = str(inputs.get("idea") or "").strip()
    # Merge only fields represented by the schema/template, never unsolicited
    # evidence, state or model-supplied authoritative totals.
    descriptions = {"summary", "problem", "solution", "target_user", "why_market", "reason"}
    metadata = {"source", "status", "day", "step_number", "name", "level", "score", "total"}

    def merge(model, default, path=""):
        if isinstance(default, dict):
            model = model if isinstance(model, dict) else {}
            return {k: merge(model.get(k), v, path + "." + k) for k, v in default.items()}
        if isinstance(default, list):
            model = model if isinstance(model, list) else []
            size = 5 if path.endswith("validation_questions") else len(default)
            if path.endswith(
                ("small_test_plan.points", "validation_before_spending", "do_not_start_with", "instead_do")
            ):
                size = min(5, max(len(model), len(default)))
            return (
                [
                    merge(
                        model[i] if i < len(model) else None,
                        default[i] if i < len(default) else default[-1],
                        path + f".{i}",
                    )
                    for i in range(size)
                ]
                if default
                else []
            )
        key = path.rsplit(".", 1)[-1]
        if (
            key.endswith("_aed")
            and isinstance(model, (int, float))
            and not isinstance(model, bool)
            and math.isfinite(model)
            and 0 <= model <= 1e12
        ):
            return model
        if isinstance(default, str):
            if key in metadata:
                return default
            missing = (
                MISSING[lang]
                if (
                    path
                    in (
                        ".summary",
                        ".idea_overview.problem",
                        ".idea_overview.solution",
                        ".idea_overview.target_user",
                        ".idea_overview.why_market",
                    )
                    or path.startswith(".opportunity_score.")
                    and key == "reason"
                )
                else default
            )
            return safe_text(model, lang, missing, minimum=3 if key == "business_name_suggestion" else 12)
        return (
            model
            if isinstance(model, (int, float)) and not isinstance(model, bool) and math.isfinite(model) and model >= 0
            else default
        )

    # Fallback identity/state always comes from the founder, never from the model.
    for key in list(plan):
        if (
            key in original
            and key not in ("state", "opportunity_score", "readiness_report")
            and not key.startswith("_")
            and not key.startswith("total_")
        ):
            plan[key] = merge(original[key], plan[key], "." + key)
    report = plan["readiness_report"]
    for key, value in list(report.items()):
        if key not in ("idea", "target_customer", "estimated_first_test_cost_aed"):
            report[key] = merge((original.get("readiness_report") or {}).get(key), value, ".readiness_report." + key)
    plan["business_name_suggestion"] = safe_text(original.get("business_name_suggestion"), lang, minimum=3) or (
        "اقتراح لم يُقدّم" if lang == "ar" else "AI name not provided"
    )
    for list_name, index_key, themes in [("seven_day_plan", "day", DAY_THEMES), ("steps", "step_number", STEP_THEMES)]:
        defaults = template_factory({}, inputs, lang)[list_name]
        for i, item in enumerate(plan[list_name]):
            item[index_key] = i + 1
            source = original.get(list_name) or []
            source = source[i] if i < len(source) and isinstance(source[i], dict) else {}
            if list_name == "seven_day_plan":
                item["focus"] = defaults[i]["focus"]
            if not re.search(themes[i], str(source.get("action", "")) + " " + str(source.get("focus", "")), re.I):
                item["action"] = defaults[i]["action"]
            if list_name == "steps":
                item["estimated_cost_aed"] = (
                    source.get("estimated_cost_aed")
                    if not offending(str(source.get("action", "")) + " " + str(source.get("description", "")))
                    and isinstance(source.get("estimated_cost_aed"), (int, float))
                    and not isinstance(source.get("estimated_cost_aed"), bool)
                    and source.get("estimated_cost_aed") >= 0
                    else None
                )
    risks = original.get("risk_radar") if isinstance(original.get("risk_radar"), list) else []
    for i, risk in enumerate(plan["risk_radar"]):
        model = risks[i] if i < len(risks) and isinstance(risks[i], dict) else {}
        reason = safe_text(model.get("reason"), lang)
        level = model.get("level")
        risk["level"] = level if reason and level in ("Low", "Medium", "High") else "Unknown"
        if i == 0 and risk["level"] == "Low":
            risk["level"] = "Medium"
    score_raw = deepcopy(original.get("opportunity_score") or {})
    for key in DIMENSIONS:
        item = score_raw.get(key)
        if isinstance(item, dict):
            item["reason"] = safe_text(item.get("reason"), lang)
            item["improve"] = safe_text(item.get("improve"), lang)
    plan["opportunity_score"] = normalize_scores(score_raw, idea, lang)
    decision = (original.get("decision_engine") or {}).get("decision")
    allowed = ("تحقق أكثر", "أعد صياغة الفكرة") if lang == "ar" else ("Validate more", "Rework the idea")
    plan["decision_engine"]["decision"] = decision if decision in allowed else allowed[0]
    plan["idea_overview"]["evidence"] = (
        "لم تُجمع أدلة من العملاء بعد. هذه فرضية للاختبار."
        if lang == "ar"
        else "No customer evidence collected yet. This is a hypothesis to test."
    )
    # Current selected customer type is authoritative. Otherwise retain the
    # model segment after safety/language checks rather than inventing evidence.
    if not inputs.get("user_type"):
        target = safe_text((original.get("readiness_report") or {}).get("target_customer"), lang)
        if target:
            report["target_customer"] = target
            plan["state"]["target_customer"] = target
    report["idea"] = idea
    plan["state"].update(
        first_action=plan["first_step_today"],
        decision=plan["decision_engine"]["decision"],
        opportunity_score=plan["opportunity_score"],
    )
    plan["pitches"] = deepcopy(original.get("pitches") or {})
    compose_pitches(plan, lang)
    plan["whatsapp_message"] = safe_text(original.get("whatsapp_message"), lang, plan["pitches"]["whatsapp"])
    plan["whatsapp_message"] = (
        re.sub(r"^(?:Khotwa|خطوة)\s*[—–-].*?(?:\.\s+|$)", "", plan["whatsapp_message"], flags=re.I)
        or plan["pitches"]["whatsapp"]
    )
    sync_costs(plan)
    return plan
