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
    return _aggregate(result)


def _aggregate(result):
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


def proof_counts(proof):
    """Validate the browser's bounded self-reports, never external evidence."""
    if proof is None:
        proof = {}
    if not isinstance(proof, dict):
        return None
    fields = ("total_responses", "interested", "maybe", "no", "stated_intent",
              "no_payment_reservations", "actual_payments", "repeat_customers")
    counts = {key: proof.get(key, 0) for key in fields}
    if any(type(value) is not int or not 0 <= value <= 10 for value in counts.values()):
        return None
    total = counts["total_responses"]
    if any(value > total for key, value in counts.items() if key != "total_responses"):
        return None
    if sum(counts[k] for k in ("interested", "maybe", "no")) > total:
        return None
    if sum(counts[k] for k in ("stated_intent", "no_payment_reservations", "actual_payments", "repeat_customers")) > total:
        return None
    return counts


def proof_evidence_text(counts, lang="en"):
    if counts is None:
        return ("تعذر استخدام أعداد وضع الإثبات. راجع الإدخالات." if lang == "ar"
                else "Proof Mode counts could not be used. Review the entries.")
    count = counts["total_responses"]
    if not count:
        return ("لم تُسجّل ملاحظات في وضع الإثبات بعد." if lang == "ar"
                else "No Proof Mode observations recorded yet.")
    return (f"{count} إجابات بإقرار المستخدم في وضع الإثبات؛ لم تُتحقق بشكل مستقل." if lang == "ar"
            else f"{count} self-reported Proof Mode responses. Not independently verified.")


def assessment_from_proof(authenticated_baseline, counts, lang="en"):
    """Mirror the existing UI rule using only authenticated base dimensions.

    Counts may change Customer Need; they cannot authenticate other dimensions
    or establish an actual payment. Submitted totals/reasons are never trusted.
    """
    result = normalize_scores(authenticated_baseline or {}, lang=lang)
    baseline_source = result["source"]
    if counts and counts["total_responses"] >= 5:
        value = (5 if counts["actual_payments"] or counts["repeat_customers"] else
                 4 if counts["no_payment_reservations"] else
                 3 if counts["stated_intent"] else 2 if counts["interested"] else 1)
        result["clear_customer"] = {
            "score": value, "status": "scored", "source": "recorded_evidence",
            "reason": ("بناءً على إدخالات المستخدم في وضع الإثبات؛ لم تُتحقق مستقلاً." if lang == "ar"
                       else "Based on user-recorded Proof Mode entries; not independently verified."),
            "improve": "اختبر السلوك مع عينة أكبر." if lang == "ar" else "Test behavior with a larger sample.",
        }
    _aggregate(result)
    # Like the dashboard, the aggregate retains its original assessment source;
    # only Customer Need gains the recorded-observation source.
    result["source"] = baseline_source
    return result
