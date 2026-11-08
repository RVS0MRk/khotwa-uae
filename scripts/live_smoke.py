"""Owner-only opt-in: two billable Groq generations, never part of mock tests."""

import argparse
from pathlib import Path
import os
import sys
import time
import json


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, child in value.items():
            if key != "bilingual_text":
                yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-live", action="store_true", help="Authorize exactly two billable API requests")
    args = parser.parse_args()
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not args.confirm_live or not key or key == "test-only-placeholder":
        parser.error("Requires --confirm-live and a real GROQ_API_KEY environment variable. No requests made.")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from prompts import build_prompt
    from plan_normalize import _normalize_plan
    from content_safety import markup
    from groq_client import request_completion, GroqGenerationError
    from config import GROQ_COMPLETION_TOKENS

    failed = False
    for lang, idea in [
        ("en", "Healthy pre-ordered lunch boxes for office workers in Abu Dhabi"),
        ("ar", "وجبات غداء صحية لموظفي المكاتب في أبوظبي"),
    ]:
        payload = {"idea": idea, "budget": 5000, "region": "Abu Dhabi", "category": "Food & Catering", "lang": lang}
        started = time.monotonic()
        try:
            system = build_prompt(lang, "professionals", "Abu Dhabi", "Food & beverage")
            user = json.dumps(payload, ensure_ascii=False)
            completion = request_completion(
                key,
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                max_completion_tokens=GROQ_COMPLETION_TOKENS["/generate"],
            )
            raw = json.loads(completion.content)
            normalized = _normalize_plan(raw, payload, lang)
            safe = [markup(s) for s in strings(raw) if markup(s)]
            retained = set(strings(normalized))
            print(
                json.dumps(
                    {
                        "language": lang,
                        "latency_seconds": round(time.monotonic() - started, 2),
                        "retention_ratio": round(sum(s in retained for s in safe) / len(safe), 4) if safe else 0,
                        "usage": completion.diagnostics,
                    },
                    ensure_ascii=True,
                )
            )
        except Exception as exc:
            failed = True
            # No provider text, user text, headers or credentials in this log.
            print(
                json.dumps(
                    {
                        "language": lang,
                        "error_type": type(exc).__name__,
                        "latency_seconds": round(time.monotonic() - started, 2),
                        "diagnostics": exc.diagnostics if isinstance(exc, GroqGenerationError) else {},
                    }
                )
            )
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
