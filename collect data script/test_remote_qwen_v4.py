"""Offline V4 contract and five-word benchmark tests."""

import csv
import hashlib
import json
import socket
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from remote_qwen_client import API_CONTRACT_VERSION, RemoteQwenClient, RemoteQwenError
from remote_qwen_probe import main
from remote_qwen_v4_benchmark import prepare_v4_benchmark, run_v4_benchmark


ROOT = Path(__file__).resolve().parents[1]
URL = "https://demo-123.trycloudflare.com"
MODEL = "Qwen/Qwen3-4B"
PROMPTS = json.loads((ROOT / "reports/image_pipeline_benchmark/20261106-image-query-v1/prompts.json").read_text(encoding="utf-8"))


class V4ClientContractTests(unittest.TestCase):
    def test_original_prompts_and_exact_4096_boundary(self):
        calls = []

        def fake(host, method, path, headers, body, timeout):
            calls.append(json.loads(body))
            response = {"model": MODEL, "text": "rice food", "input_tokens": 30,
                        "output_tokens": 2, "elapsed_seconds": 1.0}
            return 200, json.dumps(response).encode()

        client = RemoteQwenClient(URL, "placeholder", transport=fake)
        for version in ("variant_a", "variant_b"):
            system = PROMPTS[version]["system_prompt"]
            self.assertLessEqual(len(system), 4096)
            client.generate("Input: rice\nQuery:", system, 32)
            self.assertEqual(calls[-1]["system_prompt"], system)
        client.generate("rice", "x" * 4096, 32)
        self.assertEqual(len(calls[-1]["system_prompt"]), 4096)
        self.assertEqual(API_CONTRACT_VERSION, "kaggle-qwen3-4b-v4")
        self.assertEqual(len(calls), 3)
        with self.assertRaises(RemoteQwenError) as caught:
            client.generate("rice", "x" * 4097, 32)
        self.assertEqual(caught.exception.code, "contract_incompatible")
        self.assertEqual(len(calls), 3)

    def test_empty_invalid_utf8_and_independent_body_limit(self):
        for prompt, system in (("", "s"), ("rice", ""), ("rice", "x" * 4097)):
            with self.subTest(prompt=prompt[:5], system=len(system)):
                with self.assertRaises(RemoteQwenError):
                    RemoteQwenClient.validate_generation_request(prompt, system)
        prompt = "ごはん 🍚"
        body = RemoteQwenClient.validate_generation_request(prompt, "説明", 96)
        self.assertEqual(json.loads(body)["prompt"], prompt)
        with self.assertRaises(RemoteQwenError) as caught:
            RemoteQwenClient.validate_generation_request("😀" * 2100, "system", 96)
        self.assertEqual(caught.exception.code, "contract_incompatible")


class V4BenchmarkTests(unittest.TestCase):
    def test_preparation_freezes_ten_exact_requests_and_preserves_d0(self):
        d0 = ROOT / "reports/remote_qwen/d0-five-20261107"
        before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in d0.iterdir() if path.is_file()}
        with tempfile.TemporaryDirectory() as directory:
            run = prepare_v4_benchmark(ROOT, Path(directory), "d1-five-test-v4")
            manifest = json.loads((run / "experiment_manifest.json").read_text(encoding="utf-8"))
            requests = manifest["requests"]
            self.assertEqual(manifest["api_contract_version"], "kaggle-qwen3-4b-v4")
            self.assertEqual(manifest["status"], "prepared")
            self.assertEqual(len(requests), 10)
            self.assertEqual([(r["source_row_index"], r["variant"]) for r in requests],
                             [(n, variant) for n in (4, 9, 41, 54, 65) for variant in ("a", "b")])
            for request in requests:
                variant = "variant_" + request["variant"]
                self.assertEqual(request["system_prompt"], PROMPTS[variant]["system_prompt"])
                self.assertEqual(request["system_prompt_sha256"],
                                 hashlib.sha256(request["system_prompt"].encode()).hexdigest())
                self.assertEqual(request["user_prompt_sha256"],
                                 hashlib.sha256(request["user_prompt"].encode()).hexdigest())
                self.assertEqual(request["max_new_tokens"], 32 if request["variant"] == "a" else 256)
                self.assertLessEqual(len(RemoteQwenClient.validate_generation_request(
                    request["user_prompt"], request["system_prompt"], request["max_new_tokens"])), 8192)
                if request["variant"] == "a":
                    self.assertEqual(request["user_prompt"],
                                     f"Input: {request['english']}\nQuery:")
                else:
                    self.assertTrue(request["user_prompt"].startswith("Vocabulary record (JSON): "))
            with (run / "review_template.csv").open(encoding="utf-8", newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 25)
            with self.assertRaises(FileExistsError):
                prepare_v4_benchmark(ROOT, Path(directory), "d1-five-test-v4")
        after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in d0.iterdir() if path.is_file()}
        self.assertEqual(before, after)

    def test_full_budget_gate_refuses_before_any_post(self):
        for generations, seconds in ((9, 700), (10, 349)):
            calls = []

            def low_quota(host, method, path, headers, body, timeout):
                calls.append(path)
                return 200, json.dumps({"status": "ok", "model": MODEL, "gpu": "T4",
                                        "remaining_generations": generations,
                                        "remaining_seconds": seconds}).encode()

            with self.subTest(generations=generations, seconds=seconds), \
                 tempfile.TemporaryDirectory() as directory:
                run = prepare_v4_benchmark(ROOT, Path(directory), "d1-five-quota")
                with self.assertRaises(RemoteQwenError) as caught:
                    run_v4_benchmark(ROOT, run, {"QWEN_REMOTE_URL": URL,
                                                  "QWEN_REMOTE_TOKEN": "placeholder"}, transport=low_quota)
                self.assertEqual(caught.exception.code, "insufficient_quota")
                self.assertEqual(calls, ["/health"])
                self.assertFalse((run / "remote_generation").exists())

    def test_live_cli_flag_is_required(self):
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as caught:
            main(["benchmark-v4", "--run-id", "d1-five-test-v4"], environ={})
        self.assertEqual(caught.exception.code, 2)

    def test_missing_environment_refuses_before_health(self):
        calls = []

        def forbidden(*args, **kwargs):
            calls.append(args)
            raise AssertionError("network access")

        with tempfile.TemporaryDirectory() as directory:
            run = prepare_v4_benchmark(ROOT, Path(directory), "d1-five-no-env")
            with self.assertRaises(RemoteQwenError) as caught:
                run_v4_benchmark(ROOT, run, {}, transport=forbidden)
            self.assertEqual(caught.exception.code, "missing_url")
            self.assertEqual(calls, [])
            self.assertFalse((run / "remote_generation").exists())

    def test_mocked_run_makes_ten_posts_and_retains_invalid_output(self):
        posts = []
        visual = {"visual_type": "action", "search_query": "person swimming in pool",
                  "visual_description": "A person swims in a pool.",
                  "negative_constraints": [], "reason": "The action is visible."}

        def fake(host, method, path, headers, body, timeout):
            if path == "/health":
                payload = {"status": "ok", "model": MODEL, "gpu": "T4",
                           "remaining_generations": 20 - len(posts), "remaining_seconds": 700}
            else:
                request = json.loads(body)
                posts.append(request)
                result_text = ("person swimming" if request["max_new_tokens"] == 32 else
                               "{broken" if len(posts) == 2 else json.dumps(visual))
                payload = {"model": MODEL, "text": result_text, "input_tokens": 50,
                           "output_tokens": 10, "elapsed_seconds": 2.0}
            return 200, json.dumps(payload).encode()

        with tempfile.TemporaryDirectory() as directory:
            run = prepare_v4_benchmark(ROOT, Path(directory), "d1-five-success")
            summary = run_v4_benchmark(ROOT, run, {"QWEN_REMOTE_URL": URL,
                                                   "QWEN_REMOTE_TOKEN": "placeholder"}, transport=fake)
            self.assertEqual(summary["generation_calls"], 10)
            self.assertEqual(len(posts), 10)
            self.assertEqual(summary["invalid_outputs"], 1)
            records = list((run / "remote_generation").glob("*.json"))
            self.assertEqual(len(records), 10)
            failed_parse = json.loads((run / "remote_generation/004-b.json").read_text(encoding="utf-8"))
            self.assertEqual(failed_parse["response_text"], "{broken")
            self.assertEqual(failed_parse["parse_status"], "invalid")
            self.assertIsNone(failed_parse["model_revision"])
            self.assertEqual(failed_parse["eos_status"], "unavailable")
            self.assertEqual(failed_parse["finish_reason"], "unavailable")
            self.assertEqual(posts[0]["system_prompt"], PROMPTS["variant_a"]["system_prompt"])
            self.assertEqual(posts[1]["system_prompt"], PROMPTS["variant_b"]["system_prompt"])
            self.assertTrue((run / "review_ready.csv").is_file())
            self.assertNotIn("placeholder", "".join(path.read_text(encoding="utf-8")
                                               for path in run.rglob("*") if path.is_file()))

    def test_timeout_stops_partial_run_without_retry_or_restart(self):
        posts = []

        def fake(host, method, path, headers, body, timeout):
            if path == "/health":
                return 200, json.dumps({"status": "ok", "model": MODEL, "gpu": "T4",
                                        "remaining_generations": 20, "remaining_seconds": 700}).encode()
            posts.append(path)
            raise socket.timeout("ambiguous POST")

        with tempfile.TemporaryDirectory() as directory:
            run = prepare_v4_benchmark(ROOT, Path(directory), "d1-five-timeout")
            env = {"QWEN_REMOTE_URL": URL, "QWEN_REMOTE_TOKEN": "placeholder"}
            summary = run_v4_benchmark(ROOT, run, env, transport=fake)
            self.assertEqual(summary["status"], "partial")
            self.assertEqual(posts, ["/generate"])
            evidence = json.loads((run / "remote_generation/004-a.json").read_text(encoding="utf-8"))
            self.assertEqual(evidence["error"]["code"], "timeout")
            with self.assertRaises(ValueError):
                run_v4_benchmark(ROOT, run, env, transport=fake)
            self.assertEqual(posts, ["/generate"])


if __name__ == "__main__":
    unittest.main()
