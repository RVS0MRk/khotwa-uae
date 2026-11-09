"""Local, deterministic evaluation; imports no application or API configuration."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from content_safety import safe_text


def evaluate(path):
    groups = json.loads(path.read_text(encoding="utf-8"))
    results = []
    for group, sentences in groups.items():
        for sentence in sentences:
            actual = safe_text(sentence, group[-2:])
            expected = sentence if group.startswith("safe") else ""
            results.append({"group": group, "sentence": sentence, "actual": actual, "pass": actual == expected})
    summary = {}
    for kind in ("unsafe", "safe"):
        rows = [r for r in results if r["group"].startswith(kind)]
        summary[kind] = {
            "passed": sum(r["pass"] for r in rows),
            "total": len(rows),
            "rate": sum(r["pass"] for r in rows) / len(rows),
        }
    return {
        "fixture": path.name,
        # Compare content across LF/CRLF checkouts without editing the fixture.
        "fixture_sha256": hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "detector_sha256": hashlib.sha256((ROOT / "content_safety.py").read_bytes()).hexdigest(),
        "summary": summary,
        "results": results,
        "live_groq_called": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", default="tests/fixtures/v222_heldout.json")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = evaluate(ROOT / args.fixture)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        path = ROOT / args.output
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["summary"]["unsafe"]["rate"] >= 0.9 and result["summary"]["safe"]["rate"] == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
