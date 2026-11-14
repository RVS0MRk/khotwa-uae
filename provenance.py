"""Source ledger and tamper-evident publication receipts; never evidence by AI fiat."""
from copy import deepcopy
import hashlib
import hmac
import json
import os
import secrets
import re

KINDS = (
    "user_assumption", "ai_suggestion", "self_reported_observation",
    "financial_projection", "externally_verified", "unsupported",
)
_SIGNING_KEY = os.environ.get("KHOTWA_CONTENT_SIGNING_KEY", "").encode() or secrets.token_bytes(32)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sources(inputs=None, plan=None):
    """Only explicit inputs and recalculated projections enter this ledger.

    Model-supplied provenance/external-verification flags are never imported.
    No route accepts external evidence of commercial achievements in V2.2.4.
    """
    inputs, plan = inputs or {}, plan or {}
    state = plan.get("state") if isinstance(plan.get("state"), dict) else {}
    entries = {
        "guidance": {"kind": "ai_suggestion", "value": "Planning guidance, not achieved business outcomes", "verified": False},
        "unknown": {"kind": "unsupported", "value": "No external enterprise-achievement evidence supplied", "verified": False},
    }
    for name in ("idea", "budget", "region", "category", "user_type", "context"):
        value = inputs.get(name, state.get(name))
        if value not in (None, ""):
            entries["user." + name] = {"kind": "user_assumption", "value": deepcopy(value), "verified": False}
    proof = plan.get("proof_summary")
    if isinstance(proof, dict):
        counts = {k: v for k, v in proof.items() if type(v) in (int, float) and 0 <= v <= 1e12}
        entries["proof"] = {"kind": "self_reported_observation", "value": counts, "verified": False}
    if isinstance(plan.get("_financial_inputs"), dict):
        from finance import analyze, FinanceInputError
        try:
            calculated = analyze({"inputs": plan["_financial_inputs"]})["base"]
            entries["finance"] = {"kind": "financial_projection", "value": calculated, "verified": False}
        except FinanceInputError:
            pass
    return {"version": 1, "kinds": list(KINDS), "entries": entries, "external_achievement_evidence": []}


def seal(plan, ledger):
    """Receipt covers only model/application-owned text, not mutable Proof/forms."""
    from material_claims import prose_items
    hashes = sorted({f"{len(fragment)}:{digest(fragment)[:32]}" for _, value in prose_items(plan)
                     for fragment in [value, *re.split(r"(?<=[.!?؟])\s+", value)] if fragment})
    payload = {"version": 2, "strings": hashes, "ledger_hash": digest(ledger)}
    signature = hmac.new(_SIGNING_KEY, digest(payload).encode(), hashlib.sha256).hexdigest()
    plan["_content_receipt"] = {**payload, "signature": signature}
    plan["_provenance"] = ledger
    return plan


def receipt_strings(plan):
    receipt = plan.get("_content_receipt")
    if not isinstance(receipt, dict) or receipt.get("version") != 2:
        return {}
    payload = {k: receipt.get(k) for k in ("version", "strings", "ledger_hash")}
    expected = hmac.new(_SIGNING_KEY, digest(payload).encode(), hashlib.sha256).hexdigest()
    if not isinstance(receipt.get("signature"), str) or not hmac.compare_digest(expected, receipt["signature"]):
        return {}
    if payload["ledger_hash"] != digest(plan.get("_provenance")):
        return set()
    return set(payload["strings"]) if isinstance(payload["strings"], list) else set()
