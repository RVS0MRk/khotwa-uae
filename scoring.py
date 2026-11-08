"""Authoritative 25-point assessment contract. Missing information earns no points."""

from copy import deepcopy

DIMENSIONS = ("local_fit", "clear_customer", "low_starting_cost", "easy_first_step", "growth_potential")


def normalize_scores(raw, idea="", lang="en"):
    result = {}
    for key in DIMENSIONS:
        item = deepcopy(raw.get(key, {})) if isinstance(raw, dict) and isinstance(raw.get(key), dict) else {}
        value, reason = item.get("score"), item.get("reason")
        valid = (
            item.get("source") != "fallback"
            and type(value) in (int, float)
            and value in range(0, 6)
            and isinstance(reason, str)
            and len(reason.strip()) >= 12
            and reason.strip().lower() not in ("one line", "one-line reason")
            and not any(
                word in reason.lower() for word in ("insufficient information", "not assessed", "لا توجد معلومات كافية")
            )
        )
        if valid:
            item.update(score=int(value), status="provisional", source="ai_assumption")
        else:
            item.update(
                score=None,
                status="not_assessed",
                source="missing",
                reason=(
                    "معلومات غير كافية لتقييم هذا البند."
                    if lang == "ar"
                    else "Insufficient information to assess this dimension."
                ),
            )
        item.setdefault(
            "improve",
            (
                "أضف معلومات وأدلة خاصة بهذا البند."
                if lang == "ar"
                else "Add specific information and recorded evidence for this dimension."
            ),
        )
        result[key] = item
    coverage = sum(result[key]["score"] is not None for key in DIMENSIONS)
    subtotal = sum(result[key]["score"] or 0 for key in DIMENSIONS)
    result.update(
        total=subtotal if coverage == 5 else None,
        assessed_sum=subtotal,
        assessed_count=coverage,
        maximum=25,
        status="provisional" if coverage == 5 else "incomplete",
        source="ai_assumption" if coverage else "missing",
    )
    return result
