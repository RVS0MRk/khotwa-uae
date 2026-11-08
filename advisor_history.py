"""Authenticate server-produced assistant turns within an anonymous browser session."""

import hashlib
import hmac
import json
import secrets
from flask import request

_KEY = secrets.token_bytes(32)
_COOKIE = "khotwa_advisor_session"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def signature(answer, session):
    return hmac.new(_KEY, (session + "\n" + canonical(answer)).encode("utf-8"), hashlib.sha256).hexdigest()


def safe_history(history):
    session = request.cookies.get(_COOKIE)
    result = []
    for item in (history if isinstance(history, list) else [])[-8:]:
        if not isinstance(item, dict) or item.get("role") not in ("user", "assistant"):
            continue
        text = item.get("content")
        if not isinstance(text, str) or len(text) > 8000:
            continue
        if item["role"] == "assistant":
            try:
                answer = json.loads(text)
                supplied = item.get("signature")
                if (
                    not session
                    or not isinstance(supplied, str)
                    or not hmac.compare_digest(signature(answer, session), supplied)
                ):
                    continue
            except (ValueError, TypeError):
                continue
        result.append({"role": item["role"], "content": text[:1200]})
    return result
