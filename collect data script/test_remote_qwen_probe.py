"""Offline CLI and benchmark preparation tests; no Kaggle calls."""

import hashlib
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from remote_qwen_probe import main, prepare_benchmark, validate_visual_text


ROOT = Path(__file__).resolve().parents[1]
URL = "https://demo-123.trycloudflare.com"


class RemoteProbeTests(unittest.TestCase):
    def test_dry_run_never_calls_transport_or_dns(self):
        calls = []

        def forbidden(*args, **kwargs):
            calls.append(args)
            raise AssertionError("network access")

        with tempfile.TemporaryDirectory() as directory, \
             patch("socket.getaddrinfo", side_effect=forbidden):
            code = main(["dry-run", "--output", str(Path(directory) / "dry.json")],
                        environ={"QWEN_REMOTE_URL": URL, "QWEN_REMOTE_TOKEN": "secret"},
                        transport=forbidden)
            self.assertEqual(code, 0)
            self.assertEqual(calls, [])
            result = json.loads((Path(directory) / "dry.json").read_text(encoding="utf-8"))
            self.assertEqual(result["network_calls"], 0)
            self.assertEqual(result["inference_calls"], 0)
            self.assertEqual(result["variant_a_contract"], "compatible")
            self.assertEqual(result["variant_b_contract"], "compatible")
            self.assertNotIn("secret", json.dumps(result))

    def test_malformed_visual_intent_preserved_as_invalid(self):
        result = validate_visual_text("{broken")
        self.assertEqual(result["parse_status"], "invalid")
        self.assertEqual(result["response_text"], "{broken")
        self.assertTrue(result["validation_errors"])

    def test_prepare_five_stable_rows_and_subset_without_touching_sources(self):
        sources = [ROOT / "data/vocabulary/id_registry_v1.json",
                   ROOT / "data/vocabulary/semantic_decisions_v1.json",
                   ROOT / "data/query/generated_qwen.json",
                   ROOT / "reports/image_pipeline_benchmark/20261106-image-query-v1/query_experiment.json"]
        before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
        media = [path for folder in (ROOT / "data/audio", ROOT / "data/image", ROOT / "baseline")
                 for path in folder.rglob("*") if path.is_file() and "__pycache__" not in path.parts]
        media_before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in media}
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            full = prepare_benchmark(ROOT, base, "test-run-full", [4, 9, 41, 54, 65])
            manifest = json.loads((full / "experiment_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual([row["vocab_id"] for row in manifest["records"]],
                             [f"vocab-{n:06d}" for n in (4, 9, 41, 54, 65)])
            self.assertEqual(manifest["status"], "contract_incompatible")
            self.assertEqual(len((full / "review_template.csv").read_text(encoding="utf-8").splitlines()), 16)
            self.assertEqual(len(json.loads((full / "blind_mapping.json").read_text(encoding="utf-8"))["mapping"]), 15)
            small = prepare_benchmark(ROOT, base, "test-run-small", [4, 65])
            self.assertEqual(len(json.loads((small / "experiment_manifest.json").read_text(encoding="utf-8"))["records"]), 2)
            with self.assertRaises(FileExistsError):
                prepare_benchmark(ROOT, base, "test-run-small", [4])
        after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
        self.assertEqual(before, after)
        self.assertEqual(media_before,
                         {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in media})

    def test_benchmark_contract_refusal_precedes_network(self):
        calls = []

        def forbidden(*args, **kwargs):
            calls.append(args)
            raise AssertionError("network access")

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            prepare_benchmark(ROOT, base, "test-run", [4])
            code = main(["benchmark", "--live", "--run-id", "test-run"],
                        environ={"QWEN_REMOTE_URL": URL, "QWEN_REMOTE_TOKEN": "secret"},
                        transport=forbidden, output_base=base, root=ROOT)
            self.assertEqual(code, 2)
            self.assertEqual(calls, [])

    def test_mocked_future_compatible_benchmark_writes_isolated_evidence(self):
        model = "Qwen/Qwen3-4B"
        visual = {"visual_type": "food", "search_query": "cooked rice",
                  "visual_description": "A bowl of cooked rice.",
                  "negative_constraints": [], "reason": "The food is visible."}
        calls = []

        def fake(host, method, path, headers, body, timeout):
            calls.append(path)
            if path == "/health":
                response = {"status": "ok", "model": model, "gpu": "T4",
                            "remaining_generations": 2, "remaining_seconds": 100}
            else:
                response = {"model": model, "text": json.dumps(visual),
                            "input_tokens": 45, "output_tokens": 30,
                            "elapsed_seconds": 3.0}
            return 200, json.dumps(response).encode()

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run = prepare_benchmark(ROOT, base, "future-v2-fixture", [4])
            manifest_path = run / "experiment_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["system_prompt"] = "Return visual intent JSON."
            manifest["system_prompt_sha256"] = hashlib.sha256(manifest["system_prompt"].encode()).hexdigest()
            manifest["prompt_version"] = "test-short-prompt-v2"
            manifest["api_contract_version"] = "kaggle-qwen3-4b-v4"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                code = main(["benchmark", "--live", "--run-id", "future-v2-fixture"],
                            environ={"QWEN_REMOTE_URL": URL, "QWEN_REMOTE_TOKEN": "secret"},
                            transport=fake, output_base=base, root=ROOT)
            self.assertEqual(code, 0)
            self.assertEqual(calls, ["/health", "/generate"])
            evidence = json.loads((run / "remote_generation/004.json").read_text(encoding="utf-8"))
            self.assertEqual(evidence["parse_status"], "valid")
            self.assertEqual(evidence["response_text"], json.dumps(visual))
            self.assertEqual(evidence["approx_output_tokens_per_second"], 10)
            self.assertIn("cooked rice", (run / "review_ready.csv").read_text(encoding="utf-8"))
            self.assertFalse((ROOT / "reports/remote_qwen/future-v2-fixture").exists())


if __name__ == "__main__":
    unittest.main()
