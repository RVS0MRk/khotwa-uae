"""Small pure plan arithmetic and identity helpers."""

import re
import math
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def _int(v, default=0):
    try:
        if isinstance(v, bool):
            return default
        if isinstance(v, str):
            v = re.sub(r"\bAED\b|,|\s", "", v, flags=re.I)
        number = float(v)
        return int(number) if math.isfinite(number) else default
    except (TypeError, ValueError, OverflowError):
        return default


def _money(value):
    if isinstance(value, bool) or value is None:
        return None
    raw = re.sub(r"\bAED\b|,|\s", "", str(value), flags=re.I)
    if not re.fullmatch(r"\d+(?:\.\d+)?", raw):
        return None
    try:
        number = Decimal(raw).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return float(number) if number.is_finite() and number <= Decimal("1e12") else None
    except InvalidOperation:
        return None


def _sync_path_costs(plan):
    steps = plan.get("steps") or []
    costs = []
    for step in steps:
        cost = _money(step.get("estimated_cost_aed")) if isinstance(step, dict) else None
        costs.append(cost)
        if isinstance(step, dict):
            step["estimated_cost_aed"] = cost
    total = round(sum(costs), 2) if costs and all(c is not None for c in costs) else None
    budget = _money((plan.get("state") or {}).get("user_budget_aed", plan.get("_budget", 0))) or 0
    gap = round(max(0, total - budget), 2) if total is not None else None
    plan["total_estimated_cost_aed"], plan["estimated_budget_gap_aed"] = total, gap
    plan.setdefault("readiness_report", {}).update(estimated_setup_cost_aed=total, estimated_budget_gap_aed=gap)
    return plan


def _format_money(value, decimals=2):
    number = _money(value)
    if number is None:
        return "-"
    return f"{number:,.{decimals}f}".rstrip("0").rstrip(".")


def _target_customer(text, lang):
    text = str(text or "").strip()
    # Repair the observed people/business modifier ambiguity without rewriting
    # arbitrary user-entered customer descriptions.
    match = re.search(
        r"restaurant owners\s*(?:/|or)\s*(?:restaurant\s+)?marketing managers\s+with\s+(?:roughly\s+)?(\d+\s*[-–]\s*\d+)\s+seats\.?",
        text,
        re.I,
    )
    if match:
        seats = re.sub(r"\s*[-–]\s*", "-", match[1])
        return (
            f"مالكو المطاعم الصغيرة المستقلة أو مديرو تسويقها، بسعة تقارب {seats} مقعداً."
            if lang == "ar"
            else f"Owners or marketing managers of small independent restaurants with roughly {seats} seats."
        )
    return text
