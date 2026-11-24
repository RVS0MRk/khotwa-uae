"""Independent fixed-domain audit. Source override supports the frozen baseline.

No live calls: network is blocked and classifier verdicts are deliberately wrong.
The noun_phrase rows are measurements, not an assertion of perfect fact checking.
"""
import argparse
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("KHOTWA_PROBE_SOURCE", ROOT))
sys.path.insert(0, str(SOURCE))
from test_support import configure_mock_environment
configure_mock_environment()
import material_claims as gate

CASES = json.loads((ROOT / "tests/fixtures/final_language_cases.json").read_text(encoding="utf-8"))
MODES = ("planning", "hypothesis", "negation", "noun_phrase", "unknown", "missing", "malformed", "timeout")


def provider(mode):
    if mode == "timeout":
        return patch.object(gate, "classify", side_effect=TimeoutError("synthetic timeout"))
    if mode == "missing":
        return patch.object(gate, "classify", return_value={})
    return patch.object(gate, "classify", side_effect=lambda items, key: {
        item["id"]: ([] if mode == "malformed" else mode) for item in items
    })


def measure():
    records = []
    with patch("requests.post", side_effect=AssertionError("Live provider forbidden")):
        for group, fields in (("safe", ("summary", "first_step_today")),
                              ("names", ("name", "business_name_suggestion")),
                              ("unsafe", ("summary", "business_name_suggestion", "pitches.ten_sec", "personas.0.name")),
                              ("short_claims", ("name", "business_name_suggestion", "personas.0.name"))):
            for lang in ("en", "ar"):
                for mode in MODES:
                    with provider(mode):
                        for text in CASES[group][lang]:
                            for field in fields:
                                value = {"summary": text} if field == "summary" else {}
                                if field.startswith("personas"):
                                    value = {"personas": [{"name": text}]}
                                elif field.startswith("pitches"):
                                    value = {"pitches": {"ten_sec": text}}
                                else:
                                    value = {field: text}
                                clean, meta = gate.verify_model(value, {}, lang, "synthetic")
                                retained = any(v == text for p, v in gate.prose_items(clean))
                                records.append(dict(group=group, lang=lang, mode=mode, field=field,
                                                    text=text, retained=retained, status=meta["status"]))
    return {"source": str(SOURCE), "live_groq": False, "records": records,
            "summary": {f"{g}/{l}/{m}": {"retained": sum(r["retained"] for r in records if (r["group"], r["lang"], r["mode"]) == (g,l,m)),
                                                  "total": sum(1 for r in records if (r["group"],r["lang"],r["mode"]) == (g,l,m))}
                        for g in CASES for l in ("en","ar") for m in MODES}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = measure()
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
