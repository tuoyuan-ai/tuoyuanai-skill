"""Credential-free media export transport for current MCP download receipts."""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = "https://tuoyuanai.com"


class SkillError(Exception):
    def __init__(self, message, *, retryable=False):
        super().__init__(message)
        self.retryable = retryable


def emit(value, *, stream=None):
    import sys
    print(json.dumps(value, ensure_ascii=False), file=stream or sys.stdout, flush=True)


def safe_url(value):
    parts = urllib.parse.urlsplit(value)
    if parts.username or parts.password or not parts.hostname or parts.fragment:
        raise SkillError("URL must not contain credentials or a fragment.")
    if parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname in {"localhost", "127.0.0.1", "::1"}):
        raise SkillError("HTTPS is required except for local loopback acceptance.")
    return value


def origin(url):
    p = urllib.parse.urlsplit(url)
    return p.scheme, p.hostname, p.port or (443 if p.scheme == "https" else 80)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self):
        self.base = safe_url(os.environ.get("TUOYUANAI_BASE_URL", DEFAULT_BASE).rstrip("/"))
        parsed = urllib.parse.urlsplit(self.base)
        if parsed.query or parsed.path not in {"", "/"}:
            raise SkillError("TUOYUANAI_BASE_URL must be an origin without a path or query.")
        self.opener = urllib.request.build_opener(NoRedirect)

    def open(self, method, url, *, body=None, headers=None, timeout=60):
        safe_url(url)
        if any(name.lower() in {"authorization", "cookie"} for name in (headers or {})):
            raise SkillError("Media exports do not accept platform credentials.")
        request = urllib.request.Request(url, data=body, headers=dict(headers or {}), method=method)
        try:
            return self.opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            raise SkillError(f"Media download returned HTTP {exc.code}; obtain a current download receipt from MCP.") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise SkillError("Media download could not complete; successful files are preserved.") from None

    def links(self, session):
        return {"session_id": session["sessionId"], "project": session["project"],
                "project_url": self.base + session["projectUrl"]}
