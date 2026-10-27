"""Shared final-content-only Groq transport and secret-safe diagnostics."""
import json
import re
from dataclasses import dataclass

import requests
from config import GROQ_URL, MODEL


class GroqGenerationError(RuntimeError):
    def __init__(self, message, diagnostics, exception_type=None):
        super().__init__(message)
        self.diagnostics = diagnostics
        self.exception_type = exception_type or type(self).__name__


@dataclass
class GroqCompletion:
    content: str
    diagnostics: dict


def safe_api_message(message, api_key):
    if not isinstance(message, str):
        return "Groq rejected the request"
    if api_key:
        message = message.replace(api_key, "[REDACTED]")
    message = re.sub(r"(?i)\b(?:gsk_|sk-)[a-z0-9_-]+", "[REDACTED]", message)
    message = re.sub(r"(?i)\bBearer\s+\S+", "[REDACTED]", message)
    message = re.sub(r'(?i)(?:authorization|groq_api_key|api[_ -]?key|secret\.txt)\s*[=:]\s*[^,;\n]+', "[REDACTED]", message)
    return " ".join(message.split())[:500]


def request_completion(api_key, messages, *, max_completion_tokens, json_mode=True, temperature=0.7):
    diagnostics = {"http_status": None, "finish_reason": None, "content_empty": None,
                   "max_completion_tokens": max_completion_tokens}
    if not api_key:
        raise GroqGenerationError("No Groq API key configured", diagnostics)
    body = {"model": MODEL, "messages": messages, "temperature": temperature,
            "max_completion_tokens": max_completion_tokens,
            "reasoning_effort": "low", "include_reasoning": False}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    try:
        response = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {api_key}",
                                 "Content-Type": "application/json"}, json=body, timeout=40)
    except requests.RequestException as exc:
        # Network exception strings may include request details. Never log them.
        raise GroqGenerationError("Groq network request failed", diagnostics, type(exc).__name__) from None
    diagnostics["http_status"] = response.status_code
    try:
        payload = response.json()
    except ValueError:
        raise GroqGenerationError("Groq returned a non-JSON HTTP response", diagnostics, "JSONDecodeError") from None
    if response.status_code != 200:
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        message = error.get("message") if isinstance(error, dict) else None
        raise GroqGenerationError(safe_api_message(message, api_key), diagnostics, "HTTPError")
    choices = payload.get("choices") if isinstance(payload, dict) else None
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise GroqGenerationError("Groq response has no completion choice", diagnostics)
    choice = choices[0]
    reason = choice.get("finish_reason")
    diagnostics["finish_reason"] = reason if reason in ("stop", "length", "tool_calls", "content_filter", "function_call", None) else "unknown"
    message = choice.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    diagnostics["content_empty"] = not isinstance(content, str) or not content.strip()
    usage = payload.get("usage") or {}
    if isinstance(usage, dict):
        details = usage.get("completion_tokens_details") or {}
        for key, value in (("completion_tokens", usage.get("completion_tokens")),
                           ("reasoning_tokens", details.get("reasoning_tokens") if isinstance(details, dict) else None)):
            if type(value) is int and value >= 0:
                diagnostics[key] = value
    if diagnostics["content_empty"]:
        raise GroqGenerationError("Groq returned empty final message.content", diagnostics)
    if reason == "length":
        raise GroqGenerationError("Groq completion reached its token limit; final content may be truncated", diagnostics)
    # Never read, return or log message.reasoning, even if the provider sends it.
    return GroqCompletion(content.strip(), diagnostics)


def log_failure(logger, endpoint, exc, diagnostics=None):
    if isinstance(exc, GroqGenerationError):
        details = exc.diagnostics.copy()
        exception_type, message = exc.exception_type, str(exc)
    else:
        details = dict(diagnostics or {})
        exception_type = type(exc).__name__
        message = ("Invalid JSON in final message.content" if isinstance(exc, json.JSONDecodeError)
                   else "Invalid structured completion" if isinstance(exc, (ValueError, TypeError, KeyError))
                   else "Completion processing failed")
    for key in ("http_status", "finish_reason", "content_empty"):
        details.setdefault(key, None)
    details.update(endpoint=endpoint, exception_type=exception_type, safe_api_message=message)
    logger.error("Groq failure %s", json.dumps(details, ensure_ascii=True))
