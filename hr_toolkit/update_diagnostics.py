"""Bounded, local-only update diagnostics; never log credentials or raw bodies.

This module observes requests without initiating network operations. Error
classification can be used by the caller's bounded compatibility policy.
"""

from __future__ import annotations

import json
import os
import platform
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from uuid import uuid4

from hr_toolkit import __version__, runlog


_current = ContextVar("update_diagnostic", default=None)
ERROR_SAMPLE_BYTES = 4096
_GITEE_ROOT = "/api/v5/repos/optimistic-little-sunspot/hr-toolkit/releases"


def endpoint(url):
    """Keep public service identity, never URL credentials/query/custom paths."""
    try:
        parsed = urllib.parse.urlsplit(str(url))
        if parsed.scheme == "file":
            return "file://[local]"
        host = parsed.hostname or "unknown"
        if not re.fullmatch(r"[A-Za-z0-9.-]{1,253}", host):
            host = "[redacted-host]"
        path = "/[redacted-path]"
        if host == "gitee.com":
            if parsed.path in (_GITEE_ROOT, _GITEE_ROOT + "/latest"):
                path = parsed.path
            elif re.fullmatch(
                r"/optimistic-little-sunspot/hr-toolkit/releases/download/v[0-9.]+/latest\.json",
                parsed.path,
            ):
                path = parsed.path
        scheme = parsed.scheme if parsed.scheme in ("https", "http") else "other"
        return scheme + "://" + host + path
    except Exception:
        return "[invalid-endpoint]"


def version_label(value):
    text = str(value)
    return text if re.fullmatch(r"v?\d+(?:\.\d+){0,3}(?:[-+][A-Za-z0-9.-]{1,32})?", text) else "[invalid-version]"


def event(name, **fields):
    """Only callers with a diagnostic session emit events; logging is best effort."""
    try:
        state = _current.get()
        if state is None:
            return
        if name == "stage":
            state["stage"] = fields.get("stage", "unknown")
        record = {"id": state["id"], "event": name, "stage": state["stage"]}
        for key, value in fields.items():
            if value is None or isinstance(value, (bool, int, float)):
                record[key] = value
            elif isinstance(value, str):
                record[key] = value[:300]
        runlog.log_line("[更新诊断] " + json.dumps(record, ensure_ascii=False, separators=(",", ":")))
    except Exception:
        pass


def exception_fields(exc):
    """No str(exception): it may contain proxy credentials, paths or signed URLs."""
    try:
        reason = getattr(exc, "reason", exc)
        fields = {"exception": type(exc).__name__, "reason_type": type(reason).__name__}
        for key in ("errno", "winerror", "verify_code"):
            value = getattr(reason, key, None)
            if isinstance(value, int):
                fields[key] = value
        return fields
    except Exception:
        return {"exception": "unknown"}


def environment():
    try:
        windows = sys.getwindowsversion() if sys.platform == "win32" else None
        # GetVersionEx/.build can report 9200 on Windows 11 without a manifest.
        actual_version = platform.win32_ver()[1] if windows is not None else ""
        build_parts = actual_version.split(".")
        actual_build = int(build_parts[2]) if len(build_parts) >= 3 and build_parts[2].isdigit() else None
        if actual_build is None and windows is not None:
            actual_build = getattr(windows, "platform_version", (None, None, None))[2]
        event("environment", app=version_label(__version__), os=sys.platform,
              os_release=platform.release(),
              windows_build=actual_build,
              python=".".join(str(n) for n in sys.version_info[:3]),
              ssl=ssl.OPENSSL_VERSION, frozen=bool(getattr(sys, "frozen", False)),
              process_bits=64 if sys.maxsize > 2 ** 32 else 32,
              transport="urllib", proxy_values="omitted")
        # Configuration snapshot, not evidence of the actual network exit/IP.
        proxies = urllib.request.getproxies()
        event("proxy_snapshot", http_configured=bool(proxies.get("http")),
              https_configured=bool(proxies.get("https")),
              bypass_configured=bool(proxies.get("no")),
              env_proxy_present=any(value for key, value in os.environ.items()
                                    if key.lower() in ("http_proxy", "https_proxy", "all_proxy", "no_proxy")))
        opener_snapshot()
    except Exception:
        event("environment_unavailable")


def opener_snapshot():
    try:
        opener = getattr(urllib.request, "_opener", None)
        handlers = getattr(opener, "handlers", ())
        proxies = {}
        for handler in handlers:
            if isinstance(handler, urllib.request.ProxyHandler):
                proxies.update(handler.proxies)
        event("opener_snapshot", initialized=opener is not None,
              http_proxy=bool(proxies.get("http")), https_proxy=bool(proxies.get("https")))
    except Exception:
        event("opener_snapshot_unavailable")


@contextmanager
def session(operation, trigger="api"):
    # The GUI supplies manual/automatic; nested API helpers reuse its ID.
    if _current.get() is not None:
        yield
        return
    token = None
    started = time.monotonic()
    try:
        token = _current.set({"id": uuid4().hex[:16], "stage": "start", "request": 0})
        event("start", operation=operation, trigger=trigger)
        environment()
    except Exception:
        pass
    try:
        yield
    except BaseException as exc:
        event("finish", outcome="failed", elapsed_ms=int((time.monotonic() - started) * 1000),
              **exception_fields(exc))
        raise
    else:
        event("finish", outcome="completed", elapsed_ms=int((time.monotonic() - started) * 1000))
    finally:
        if token is not None:
            _current.reset(token)


def operation(name):
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with session(name):
                return function(*args, **kwargs)
        return wrapped
    return decorate


def next_request():
    try:
        state = _current.get()
        if state is not None:
            state["request"] += 1
            return state["request"]
    except Exception:
        pass
    return 0


def response_info(response, request_number, requested_url):
    try:
        headers = getattr(response, "headers", None) or {}
        fields = {}
        # Explicit allowlist; never dump all headers, Set-Cookie or Location.
        for key in ("Content-Type", "Retry-After", "X-Request-Id", "X-Correlation-Id",
                    "X-Ratelimit-Remaining", "X-Ratelimit-Reset", "CF-Ray", "Server"):
            value = str(headers.get(key, ""))
            if value and len(value) <= 160 and re.fullmatch(r"[A-Za-z0-9 ._:;,/+=()-]+", value):
                fields[key.lower()] = value
        geturl = getattr(response, "geturl", None)
        final_url = geturl() if callable(geturl) else None
        status = getattr(response, "status", getattr(response, "code", None))
        event("response", request=request_number, status=status if isinstance(status, int) else None,
              final_endpoint=endpoint(final_url or requested_url),
              redirected=bool(final_url and final_url != requested_url), **fields)
        opener_snapshot()
    except Exception:
        event("response_details_unavailable", request=request_number)


def error_sample(response, request_number):
    """Read at most one small buffer using the existing request timeout.

    Returns True only for known HTML WAF content without a rate-limit marker.
    Only fixed classifications leave this function. A marker is evidence of a
    response type, NOT proof of the remote firewall's rule or who configured it.
    """
    try:
        headers = getattr(response, "headers", None) or {}
        encoding = str(headers.get("Content-Encoding", "identity")).lower()
        reader = getattr(response, "read1", None)
        if encoding not in ("", "identity") or not callable(reader):
            event("error_sample", request=request_number, sample="unavailable")
            return False
        raw = reader(ERROR_SAMPLE_BYTES)
        text = raw.decode("utf-8-sig", errors="replace").lower()
        stripped = text.lstrip()
        kind = "empty" if not raw else "other"
        if stripped.startswith(("{", "[")):
            kind = "json_like"
        elif "<html" in text or "<!doctype html" in text:
            kind = "html"
        waf = "baidu_waf_intercept_page" in text
        rate_limit = any(marker in text for marker in (
            "rate limit", "rate_limit", "too many requests", "访问频率", "请求过于频繁"))
        event("error_sample", request=request_number, sample="read", sampled_bytes=len(raw),
              sample_at_limit=len(raw) >= ERROR_SAMPLE_BYTES, body_kind=kind,
              waf_marker=waf, rate_limit_marker=rate_limit)
        return kind == "html" and waf and not rate_limit
    except Exception as exc:
        event("error_sample", request=request_number, sample="unavailable", **exception_fields(exc))
        return False
