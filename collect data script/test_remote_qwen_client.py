"""Offline contract tests for the opt-in Qwen3-4B HTTP client."""

import json
import socket
import unittest
from unittest.mock import patch

from remote_qwen_client import RemoteQwenClient, RemoteQwenError, _direct_https


URL = "https://demo-123.trycloudflare.com"
MODEL = "Qwen/Qwen3-4B"
HEALTH = {"status": "ok", "model": MODEL, "gpu": "Tesla T4",
          "remaining_generations": 18, "remaining_seconds": 700}
GENERATED = {"model": MODEL, "text": "A bowl of cooked rice.",
             "input_tokens": 28, "output_tokens": 12, "elapsed_seconds": 2.5}


class FakeTransport:
    def __init__(self, status=200, response=None, error=None):
        self.status = status
        self.response = response if response is not None else HEALTH
        self.error = error
        self.calls = []

    def __call__(self, host, method, path, headers, body, timeout):
        self.calls.append((host, method, path, body, timeout))
        if self.error:
            raise self.error
        payload = self.response if isinstance(self.response, bytes) else json.dumps(self.response).encode()
        return self.status, payload


class RemoteClientTests(unittest.TestCase):
    def test_valid_health_and_generation(self):
        fake = FakeTransport()
        client = RemoteQwenClient(URL, "secret", transport=fake)
        health = client.health()
        self.assertEqual(health["remaining_generations"], 18)
        self.assertGreaterEqual(health["round_trip_seconds"], 0)
        fake.response = GENERATED
        result = client.generate("Describe rice", "Vocabulary assistant", 96)
        self.assertEqual(result["text"], GENERATED["text"])
        self.assertEqual(result["model"], MODEL)
        self.assertEqual(result["approx_output_tokens_per_second"], 4.8)
        self.assertEqual([call[1:3] for call in fake.calls], [("GET", "/health"), ("POST", "/generate")])
        self.assertEqual(json.loads(fake.calls[1][3]), {"prompt": "Describe rice",
                         "system_prompt": "Vocabulary assistant", "max_new_tokens": 96})

    def test_missing_or_invalid_token_never_leaks(self):
        for token in (None, "", "bad\r\ntoken"):
            with self.subTest(token=token):
                with self.assertRaises(RemoteQwenError) as caught:
                    RemoteQwenClient(URL, token)
                self.assertEqual(caught.exception.code, "missing_token" if not token else "invalid_token")
                self.assertNotIn("bad", str(caught.exception))

    def test_missing_or_unsafe_endpoint(self):
        for url in (None, "", "http://demo.trycloudflare.com", "https://localhost",
                    "https://127.0.0.1", "https://a.b.trycloudflare.com",
                    "https://trycloudflare.com", "https://bad-.trycloudflare.com",
                    "https://user:pass@demo.trycloudflare.com", "https://demo.trycloudflare.com:443",
                    "https://demo.trycloudflare.com/path", "https://demo.trycloudflare.com?x=1",
                    "https://demo.trycloudflare.com#x", "https://demo.trycloudflare.com/",
                    "https://demo.trycloudflare.com.evil.test"):
            with self.subTest(url=url), self.assertRaises(RemoteQwenError):
                RemoteQwenClient(url, "secret")

    def test_configured_model_is_fixed(self):
        with self.assertRaises(RemoteQwenError) as caught:
            RemoteQwenClient(URL, "secret", expected_model="Qwen/Qwen3-1.7B")
        self.assertEqual(caught.exception.code, "model_mismatch")

    def test_redirect_rejected_without_following(self):
        fake = FakeTransport(status=302, response=b"", error=None)
        client = RemoteQwenClient(URL, "secret", transport=fake)
        with self.assertRaises(RemoteQwenError) as caught:
            client.health()
        self.assertEqual(caught.exception.code, "redirect_rejected")
        self.assertEqual(len(fake.calls), 1)

    def test_timeout_has_no_generation_retry(self):
        fake = FakeTransport(error=socket.timeout("timed out"))
        client = RemoteQwenClient(URL, "secret", transport=fake)
        with self.assertRaises(RemoteQwenError) as caught:
            client.generate("rice", "system", 96)
        self.assertEqual(caught.exception.code, "timeout")
        self.assertEqual(len(fake.calls), 1)

    def test_http_errors_are_classified_and_safe(self):
        for status, code in ((400, "invalid_request"), (401, "unauthorized"),
                             (429, "quota_or_busy"), (502, "upstream_failure"),
                             (503, "remote_unavailable"), (504, "upstream_failure")):
            fake = FakeTransport(status=status, response=b"secret Authorization: Bearer secret")
            with self.subTest(status=status), self.assertRaises(RemoteQwenError) as caught:
                RemoteQwenClient(URL, "secret", transport=fake).health()
            self.assertEqual(caught.exception.code, code)
            self.assertNotIn("secret", str(caught.exception))

    def test_connection_failure(self):
        fake = FakeTransport(error=OSError("private host unavailable"))
        with self.assertRaises(RemoteQwenError) as caught:
            RemoteQwenClient(URL, "secret", transport=fake).health()
        self.assertEqual(caught.exception.code, "connection_failure")

    def test_invalid_json_or_response_size(self):
        for payload, code in ((b"{bad", "invalid_json"), (b"x" * 65537, "response_too_large")):
            with self.subTest(code=code), self.assertRaises(RemoteQwenError) as caught:
                RemoteQwenClient(URL, "secret", transport=FakeTransport(response=payload)).health()
            self.assertEqual(caught.exception.code, code)

    def test_wrong_field_types_and_model_mismatch(self):
        for response, code in (({**HEALTH, "remaining_generations": True}, "unexpected_schema"),
                               ({**GENERATED, "output_tokens": "12"}, "unexpected_schema"),
                               ({**GENERATED, "model": "Qwen/Qwen3-1.7B"}, "model_mismatch"),
                               ({**GENERATED, "text": ""}, "invalid_generated_output")):
            with self.subTest(code=code), self.assertRaises(RemoteQwenError) as caught:
                client = RemoteQwenClient(URL, "secret", transport=FakeTransport(response=response))
                (client.health() if "remaining_generations" in response else
                 client.generate("rice", "system", 96))
            self.assertEqual(caught.exception.code, code)

    def test_request_limits_are_rejected_before_transport(self):
        fake = FakeTransport(response=GENERATED)
        client = RemoteQwenClient(URL, "secret", transport=fake)
        for prompt, system, tokens in (("x" * 3001, "s", 96), ("x", "s" * 4097, 96),
                                       ("x", "s", 257), ("x", "s", 0)):
            with self.subTest(length=len(prompt), system=len(system), tokens=tokens):
                with self.assertRaises(RemoteQwenError) as caught:
                    client.generate(prompt, system, tokens)
                self.assertEqual(caught.exception.code, "contract_incompatible")
        self.assertEqual(fake.calls, [])

    def test_utf8_body_limit_is_measured_in_bytes(self):
        fake = FakeTransport(response=GENERATED)
        client = RemoteQwenClient(URL, "secret", transport=fake)
        with self.assertRaises(RemoteQwenError) as caught:
            client.generate("😀" * 2500, "s" * 800, 96)
        self.assertEqual(caught.exception.code, "contract_incompatible")
        self.assertEqual(fake.calls, [])

    def test_private_dns_answer_rejected_before_connect(self):
        answer = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]
        with patch("remote_qwen_client.socket.getaddrinfo", return_value=answer), \
             patch("remote_qwen_client.http.client.HTTPSConnection") as connection:
            with self.assertRaises(RemoteQwenError) as caught:
                _direct_https("demo-123.trycloudflare.com", "GET", "/health", {}, None, 1)
        self.assertEqual(caught.exception.code, "invalid_host_address")
        connection.assert_not_called()

    def test_quota_preflight(self):
        for changes in ({"remaining_generations": 0}, {"remaining_seconds": 10}):
            with self.subTest(changes=changes), self.assertRaises(RemoteQwenError) as caught:
                RemoteQwenClient.require_capacity({**HEALTH, **changes}, min_seconds=30)
            self.assertEqual(caught.exception.code, "insufficient_quota")


if __name__ == "__main__":
    unittest.main()
