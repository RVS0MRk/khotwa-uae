"""Count actual paid provider attempts, including verification, per worker.

The existing logical-route limiter remains separate. A second semantic request
must not silently double the configured production provider-call allowance.
"""
import os
import time
import ipaddress
from collections import deque
from threading import Lock

_windows = {}
_lock = Lock()


def reserve():
    from flask import has_request_context, request
    if os.environ.get("RENDER") != "true" or not has_request_context():
        return 0
    candidate = request.headers.get("X-Forwarded-For", "").rsplit(",", 1)[-1].strip()
    try:
        client = str(ipaddress.ip_address(candidate))
    except ValueError:
        client = request.remote_addr or "unknown"
    def limit(name, default):
        try:
            value = int(os.environ.get(name, default))
            return value if 1 <= value <= 100000 else default
        except ValueError:
            return default
    quotas = [("global", limit("KHOTWA_AI_GLOBAL_PER_10MIN", 400)), (client, limit("KHOTWA_AI_CLIENT_PER_10MIN", 30))]
    now = time.monotonic()
    with _lock:
        for key in list(_windows):
            if not _windows[key] or now-_windows[key][-1] >= 600:
                del _windows[key]
        for key, _ in quotas:
            queue = _windows.setdefault(key, deque())
            while queue and now-queue[0] >= 600:
                queue.popleft()
        wait = max([600-(now-_windows[key][0]) for key, maximum in quotas if len(_windows[key]) >= maximum] or [0])
        if wait:
            return min(600, max(1, int(wait)+1))
        for key, _ in quotas:
            _windows[key].append(now)
    return 0
