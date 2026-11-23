"""Minimal, opt-in HTTPS client for the Kaggle Qwen3-4B demo API."""

from __future__ import annotations

import http.client
import ipaddress
import json
import math
import re
import socket
import time
from urllib.parse import urlsplit


MODEL_ID = "Qwen/Qwen3-4B"
API_CONTRACT_VERSION = "kaggle-qwen3-4b-v4"
MAX_SYSTEM_PROMPT_CHARS = 4096
MAX_RESPONSE_BYTES = 65536
_HOST = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.trycloudflare\.com\Z", re.ASCII)


class RemoteQwenError(Exception):
    """A classified failure; messages and attributes never contain credentials."""

    def __init__(self, code: str, message: str, *, http_status: int | None = None,
                 round_trip_seconds: float | None = None):
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.round_trip_seconds = round_trip_seconds

    def as_dict(self) -> dict:
        return {"code": self.code, "message": str(self), "http_status": self.http_status,
                "round_trip_seconds": self.round_trip_seconds}


def validate_url(value: str | None) -> str:
    if not value:
        raise RemoteQwenError("missing_url", "QWEN_REMOTE_URL is required")
    if not isinstance(value, str):
        raise RemoteQwenError("invalid_url", "Remote URL must be HTTPS on one trycloudflare subdomain")
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise RemoteQwenError("invalid_url", "Invalid remote URL") from None
    if (parsed.scheme != "https" or not host or not _HOST.fullmatch(host)
            or parsed.netloc != host or port is not None or parsed.path or parsed.query
            or parsed.fragment or value != f"https://{host}"):
        raise RemoteQwenError("invalid_url", "Remote URL must be HTTPS on one trycloudflare subdomain, without port or path")
    return host


def _direct_https(host: str, method: str, path: str, headers: dict,
                  body: bytes | None, timeout: float) -> tuple[int, bytes]:
    """Resolve once, reject nonpublic answers, and connect to a checked address."""
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise RemoteQwenError("invalid_host_address", "Tunnel DNS returned a nonpublic address")
    address = addresses[0][4][0]
    connection = http.client.HTTPSConnection(host, 443, timeout=timeout)
    # HTTPSConnection keeps the hostname for TLS SNI and certificate validation.
    connection._create_connection = lambda _target, limit, source_address=None: socket.create_connection(
        (address, 443), limit, source_address)
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        if response.status >= 300:
            return response.status, b""
        return response.status, response.read(MAX_RESPONSE_BYTES + 1)
    finally:
        connection.close()


def _number(value: object) -> bool:
    return ((type(value) is int and 0 <= value <= 1_000_000_000) or
            (type(value) is float and math.isfinite(value) and 0 <= value <= 1_000_000_000))


def _count(value: object) -> bool:
    return type(value) is int and 0 <= value <= 1_000_000_000


class RemoteQwenClient:
    def __init__(self, url: str | None, token: str | None, *, timeout: float = 30,
                 expected_model: str = MODEL_ID, transport=None):
        if expected_model != MODEL_ID:
            raise RemoteQwenError("model_mismatch", "Remote client requires Qwen/Qwen3-4B")
        self.host = validate_url(url)
        if not token:
            raise RemoteQwenError("missing_token", "QWEN_REMOTE_TOKEN is required")
        if (not isinstance(token, str) or len(token) > 2048 or not token.isascii()
                or any(char.isspace() or ord(char) < 33 or ord(char) > 126 for char in token)):
            raise RemoteQwenError("invalid_token", "Bearer token contains invalid characters")
        if not _number(timeout) or timeout == 0:
            raise RemoteQwenError("invalid_timeout", "Timeout must be positive")
        self._token = token
        self.timeout = timeout
        self._transport = transport or _direct_https

    def _request(self, method: str, path: str, payload: bytes | None = None) -> dict:
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        started = time.perf_counter()
        try:
            status, body = self._transport(self.host, method, path, headers, payload, self.timeout)
        except RemoteQwenError:
            raise
        except (socket.timeout, TimeoutError):
            raise RemoteQwenError("timeout", "Remote request timed out; generation was not retried",
                                  round_trip_seconds=time.perf_counter() - started) from None
        except (OSError, http.client.HTTPException):
            raise RemoteQwenError("connection_failure", "Remote connection failed",
                                  round_trip_seconds=time.perf_counter() - started) from None
        elapsed = time.perf_counter() - started
        if 300 <= status < 400:
            raise RemoteQwenError("redirect_rejected", "Remote redirect rejected", http_status=status,
                                  round_trip_seconds=elapsed)
        failures = {400: ("invalid_request", "Remote rejected the request"),
                    401: ("unauthorized", "Remote authentication failed"),
                    429: ("quota_or_busy", "Remote quota exhausted or model busy"),
                    502: ("upstream_failure", "Remote upstream failed"),
                    503: ("remote_unavailable", "Remote session unavailable"),
                    504: ("upstream_failure", "Remote upstream timed out")}
        if status != 200:
            code, message = failures.get(status, ("model_failure", "Remote model request failed"))
            raise RemoteQwenError(code, message, http_status=status, round_trip_seconds=elapsed)
        if len(body) > MAX_RESPONSE_BYTES:
            raise RemoteQwenError("response_too_large", "Remote JSON response exceeds size limit",
                                  round_trip_seconds=elapsed)
        try:
            document = json.loads(body)
        except (UnicodeError, json.JSONDecodeError):
            raise RemoteQwenError("invalid_json", "Remote response is not valid JSON",
                                  round_trip_seconds=elapsed) from None
        if not isinstance(document, dict):
            raise RemoteQwenError("unexpected_schema", "Remote response must be a JSON object",
                                  round_trip_seconds=elapsed)
        if document.get("model") != MODEL_ID:
            raise RemoteQwenError("model_mismatch", "Remote response model ID mismatch",
                                  round_trip_seconds=elapsed)
        document["round_trip_seconds"] = round(elapsed, 6)
        return document

    def health(self) -> dict:
        result = self._request("GET", "/health")
        if (result.get("status") != "ok" or not _count(result.get("remaining_generations"))
                or not _number(result.get("remaining_seconds"))
                or not isinstance(result.get("gpu"), str)):
            raise RemoteQwenError("unexpected_schema", "Remote health response has unexpected fields")
        return result

    @staticmethod
    def require_capacity(health: dict, *, min_seconds: float = 30) -> None:
        if (health["remaining_generations"] < 1 or
                health["remaining_seconds"] < min_seconds):
            raise RemoteQwenError("insufficient_quota", "Insufficient generation quota or session time")

    @staticmethod
    def validate_generation_request(prompt: str, system_prompt: str,
                                    max_new_tokens: int = 96) -> bytes:
        if (not isinstance(prompt, str) or not prompt or len(prompt) > 3000
                or not isinstance(system_prompt, str) or not system_prompt
                or len(system_prompt) > MAX_SYSTEM_PROMPT_CHARS or type(max_new_tokens) is not int
                or not 1 <= max_new_tokens <= 256):
            raise RemoteQwenError("contract_incompatible", "Generation input exceeds Kaggle API V4 limits")
        body = json.dumps({"prompt": prompt, "system_prompt": system_prompt,
                           "max_new_tokens": max_new_tokens}, ensure_ascii=False).encode("utf-8")
        if len(body) > 8192:
            raise RemoteQwenError("contract_incompatible", "Generation request body exceeds 8192 bytes")
        return body

    def generate(self, prompt: str, system_prompt: str, max_new_tokens: int = 96) -> dict:
        body = self.validate_generation_request(prompt, system_prompt, max_new_tokens)
        result = self._request("POST", "/generate", body)
        if (not isinstance(result.get("text"), str)
                or not _count(result.get("input_tokens"))
                or not _count(result.get("output_tokens"))
                or not _number(result.get("elapsed_seconds"))):
            raise RemoteQwenError("unexpected_schema", "Remote generation response has unexpected fields")
        if not result["text"].strip():
            raise RemoteQwenError("invalid_generated_output", "Remote model returned empty text")
        elapsed = result["elapsed_seconds"]
        result["approx_output_tokens_per_second"] = (
            round(result["output_tokens"] / elapsed, 3) if elapsed else None)
        return result
