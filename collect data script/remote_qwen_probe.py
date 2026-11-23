"""Offline preparation and explicit opt-in diagnostics for the remote Qwen demo."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from collector_common import PROJECT_ROOT
from image_query_benchmark import (PROMPT_B_VERSION, VISUAL_PROMPT, load_inputs,
                                   parse_visual_output, validate_experiment_document,
                                   verify_hashes)
from query_generator import SYSTEM_PROMPT
from remote_qwen_client import (API_CONTRACT_VERSION, MAX_SYSTEM_PROMPT_CHARS,
                                MODEL_ID, RemoteQwenClient,
                                RemoteQwenError, validate_url)


DEFAULT_IDS = (4, 9, 41, 54, 65)
LEGACY_API_CONTRACT_VERSION = "kaggle-qwen3-4b-v1"
SOURCE_EXPERIMENT = Path("reports/image_pipeline_benchmark/20261106-image-query-v1/query_experiment.json")
INPUT_FILES = (Path("data/vocabulary/en.txt"), Path("data/vocabulary/jp.txt"),
               Path("data/vocabulary/vn.txt"), Path("data/vocabulary/id_registry_v1.json"),
               Path("data/vocabulary/semantic_decisions_v1.json"),
               Path("data/vocabulary/unified_dataset_v1.json"), SOURCE_EXPERIMENT,
               Path("reports/image_pipeline_benchmark/20261106-image-query-v1/prompts.json"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_new_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def validate_visual_text(text: str) -> dict:
    # The API omits finish_reason/EOS. This is structural validation only.
    parsed = parse_visual_output(text, ended=True)
    return {"response_text": text, "parse_status": parsed["validation_status"],
            "parsed": parsed["parsed"], "validation_errors": [parsed["error"]] if parsed["error"] else [],
            "eos_status": "unknown"}


def _user_prompt(row: dict) -> str:
    context = {key: row[key] for key in
               ("english", "japanese", "vietnamese", "semantic_review_status",
                "target_sense", "image_search_intent", "usage_note")}
    return "Vocabulary record (JSON): " + json.dumps(context, ensure_ascii=False)


def prepare_benchmark(root: Path, output_base: Path, run_id: str,
                      selected_numbers: list[int]) -> Path:
    """Freeze five or fewer canonical comparisons in a new, isolated directory."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{5,79}", run_id):
        raise ValueError("Unsafe run ID")
    if not selected_numbers or len(selected_numbers) > 5 or len(set(selected_numbers)) != len(selected_numbers):
        raise ValueError("Select one to five distinct source rows")
    if any(number not in DEFAULT_IDS for number in selected_numbers):
        raise ValueError("Only source rows 004, 009, 041, 054 and 065 are in D0 scope")
    root = root.resolve()
    source = json.loads((root / SOURCE_EXPERIMENT).read_text(encoding="utf-8"))
    verify_hashes(root, source["input_hashes"])
    validate_experiment_document(source)
    canonical = {row["source_row_index"]: row for row in load_inputs(root)}
    old = {row["source_row_index"]: row for row in source["records"]}
    records = []
    for number in selected_numbers:
        row, prior = canonical[number], old[number]
        if row["vocab_id"] != prior["vocab_id"]:
            raise ValueError("Historical and canonical vocabulary IDs differ")
        records.append({"source_row_index": number, "vocab_id": row["vocab_id"],
                        "english": row["english"], "japanese": row["japanese"],
                        "vietnamese": row["vietnamese"],
                        "semantic_review_status": row["semantic_review_status"],
                        "target_sense": row["target_sense"],
                        "image_search_intent": row["image_search_intent"],
                        "usage_note": row["usage_note"],
                        "historical_1_7b": prior["historical"],
                        "variant_b_1_7b": prior["variant_b"],
                        "submitted_prompt": _user_prompt(row)})
    hashes = {path.as_posix(): hashlib.sha256((root / path).read_bytes()).hexdigest()
              for path in INPUT_FILES}
    run_dir = output_base / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest = {"schema_version": 1, "run_id": run_id, "status": "contract_incompatible",
                "prepared_at_utc": _now(), "remote_provider": "kaggle_gpu_cloudflare_quick_tunnel",
                "requested_model": MODEL_ID, "api_contract_version": LEGACY_API_CONTRACT_VERSION,
                "prompt_version": PROMPT_B_VERSION,
                "system_prompt": VISUAL_PROMPT,
                "system_prompt_sha256": hashlib.sha256(VISUAL_PROMPT.encode()).hexdigest(),
                "system_prompt_characters": len(VISUAL_PROMPT),
                "generation_parameters": {"max_new_tokens": 256, "decoding": "greedy",
                                          "thinking": False},
                "model_revision": None, "input_hashes": hashes, "records": records,
                "contract_blocker": "Variant B system prompt is 1560 characters; API v1 limit is 800"}
    _write_new_json(run_dir / "experiment_manifest.json", manifest)
    candidates = []
    for row in records:
        for variant, query in (("historical_1_7b", row["historical_1_7b"]["effective_search_query"]),
                               ("variant_b_1_7b", row["variant_b_1_7b"]["parsed_query"]),
                               ("remote_4b", None)):
            candidates.append((row, variant, query))
    random.Random(20261107).shuffle(candidates)
    mapping = []
    with (run_dir / "review_template.csv").open("x", encoding="utf-8", newline="") as handle:
        columns = ("review_id", "vocab_id", "english", "japanese", "vietnamese",
                   "candidate_query", "candidate_available", "correct_intended_meaning",
                   "visibly_depictable", "ambiguous_or_wrong_sense", "reviewer_rationale",
                   "reviewer_id", "reviewed_at")
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for index, (row, variant, query) in enumerate(candidates, 1):
            review_id = f"R{index:03d}"
            writer.writerow({"review_id": review_id, "vocab_id": row["vocab_id"],
                             "english": row["english"], "japanese": row["japanese"]["display"],
                             "vietnamese": row["vietnamese"], "candidate_query": query or "",
                             "candidate_available": bool(query)})
            mapping.append({"review_id": review_id, "vocab_id": row["vocab_id"],
                            "variant": variant})
    _write_new_json(run_dir / "blind_mapping.json", {"schema_version": 1,
                                                       "seed": 20261107, "mapping": mapping})
    return run_dir


def _client(environ: dict, transport=None) -> RemoteQwenClient:
    return RemoteQwenClient(environ.get("QWEN_REMOTE_URL"),
                            environ.get("QWEN_REMOTE_TOKEN"), transport=transport)


def _run_benchmark(run_dir: Path, root: Path, environ: dict, transport=None) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{5,79}", run_dir.name):
        raise ValueError("Unsafe run ID")
    manifest = json.loads((run_dir / "experiment_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or manifest.get("requested_model") != MODEL_ID:
        raise ValueError("Invalid remote experiment manifest")
    verify_hashes(root, manifest["input_hashes"])
    if hashlib.sha256(manifest["system_prompt"].encode()).hexdigest() != manifest["system_prompt_sha256"]:
        raise ValueError("Saved system prompt hash mismatch")
    if manifest.get("api_contract_version") == LEGACY_API_CONTRACT_VERSION:
        raise RemoteQwenError("contract_incompatible", "D0 run is frozen to API v1; prepare a new V4 run")
    if len(manifest["system_prompt"]) > 800:
        raise RemoteQwenError("contract_incompatible", "Saved Variant B system prompt exceeds API v1 limit")
    for row in manifest["records"]:
        RemoteQwenClient.validate_generation_request(row["submitted_prompt"],
                                                     manifest["system_prompt"], 256)
    if (run_dir / "execution_summary.json").exists() or (run_dir / "remote_generation").exists():
        raise ValueError("Run already has generation evidence; create a new run")
    client = _client(environ, transport)
    started = time.perf_counter()
    results = []
    (run_dir / "remote_generation").mkdir()
    for row in manifest["records"]:
        evidence = {"vocab_id": row["vocab_id"], "source_row_index": row["source_row_index"],
                    "requested_model": MODEL_ID, "returned_model": None,
                    "remote_provider": manifest["remote_provider"],
                    "api_contract_version": manifest["api_contract_version"],
                    "prompt_version": manifest["prompt_version"],
                    "submitted_prompt": row["submitted_prompt"],
                    "system_prompt": manifest["system_prompt"],
                    "generation_parameters": manifest["generation_parameters"],
                    "model_revision": None, "executed_at_utc": _now()}
        try:
            health = client.health()
            client.require_capacity(health, min_seconds=client.timeout + 5)
            evidence["remaining_generations_before"] = health["remaining_generations"]
            evidence["remaining_seconds_before"] = health["remaining_seconds"]
            evidence["health_round_trip_seconds"] = health["round_trip_seconds"]
            result = client.generate(row["submitted_prompt"], manifest["system_prompt"], 256)
            evidence.update({"returned_model": result["model"], "request_duration_seconds": result["round_trip_seconds"],
                             "server_elapsed_seconds": result["elapsed_seconds"],
                             "input_tokens": result["input_tokens"], "output_tokens": result["output_tokens"],
                             "approx_output_tokens_per_second": result["approx_output_tokens_per_second"],
                             **validate_visual_text(result["text"]), "request_status": "success"})
        except RemoteQwenError as exc:
            evidence.update({"request_status": "failed", "error": exc.as_dict(),
                             "parse_status": "not_available", "validation_errors": []})
        _write_new_json(run_dir / "remote_generation" / f"{row['source_row_index']:03d}.json", evidence)
        results.append(evidence)
        if evidence["request_status"] == "failed":
            break
    summary = {"schema_version": 1, "run_id": manifest["run_id"],
               "completed_at_utc": _now(), "total_wall_seconds": round(time.perf_counter() - started, 6),
               "requested_count": len(manifest["records"]), "attempted_count": len(results),
               "successful_requests": sum(r["request_status"] == "success" for r in results),
               "failed_requests": sum(r["request_status"] == "failed" for r in results),
               "valid_visual_outputs": sum(r.get("parse_status") == "valid" for r in results),
               "status": "complete" if len(results) == len(manifest["records"]) and
               all(r["request_status"] == "success" for r in results) else "partial"}
    _write_new_json(run_dir / "execution_summary.json", summary)
    mapping = {item["review_id"]: item for item in
               json.loads((run_dir / "blind_mapping.json").read_text(encoding="utf-8"))["mapping"]}
    remote = {item["vocab_id"]: item for item in results}
    with (run_dir / "review_template.csv").open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        with (run_dir / "review_ready.csv").open("x", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=reader.fieldnames)
            writer.writeheader()
            for item in reader:
                if mapping[item["review_id"]]["variant"] == "remote_4b":
                    result = remote.get(item["vocab_id"], {})
                    parsed = result.get("parsed") or {}
                    item["candidate_query"] = parsed.get("search_query", "")
                    item["candidate_available"] = str(bool(item["candidate_query"]))
                writer.writerow(item)
    return summary


def main(argv: list[str] | None = None, *, environ: dict | None = None,
         transport=None, output_base: Path | None = None, root: Path = PROJECT_ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("config")
    dry = actions.add_parser("dry-run")
    dry.add_argument("--output", type=Path)
    health = actions.add_parser("health")
    health.add_argument("--live", action="store_true", required=True)
    health.add_argument("--output", type=Path)
    generate = actions.add_parser("generate")
    generate.add_argument("--live", action="store_true", required=True)
    generate.add_argument("--prompt", required=True)
    generate.add_argument("--system-prompt", required=True)
    generate.add_argument("--max-new-tokens", type=int, default=96)
    generate.add_argument("--output", type=Path)
    prepare = actions.add_parser("prepare")
    prepare.add_argument("--run-id", required=True)
    prepare.add_argument("--vocab-id", action="append")
    prepare_v4 = actions.add_parser("prepare-v4")
    prepare_v4.add_argument("--run-id", default="d1-five-20261107-qwen4b-v4")
    benchmark = actions.add_parser("benchmark")
    benchmark.add_argument("--live", action="store_true", required=True)
    benchmark.add_argument("--run-id", required=True)
    benchmark_v4 = actions.add_parser("benchmark-v4")
    benchmark_v4.add_argument("--live", action="store_true", required=True)
    benchmark_v4.add_argument("--run-id", default="d1-five-20261107-qwen4b-v4")
    args = parser.parse_args(argv)
    env = os.environ if environ is None else environ
    root = root.resolve()
    base = output_base or root / "reports/remote_qwen"
    try:
        if args.action == "prepare-v4":
            from remote_qwen_v4_benchmark import prepare_v4_benchmark
            directory = prepare_v4_benchmark(root, base, args.run_id)
            print(json.dumps({"prepared_run": str(directory), "status": "prepared",
                              "generation_calls": 10}))
            return 0
        if args.action == "benchmark-v4":
            from remote_qwen_v4_benchmark import run_v4_benchmark
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{5,79}", args.run_id):
                raise ValueError("Unsafe run ID")
            print(json.dumps(run_v4_benchmark(root, base / args.run_id, env, transport)))
            return 0
        if args.action == "prepare":
            numbers = [int(value) for value in args.vocab_id] if args.vocab_id else list(DEFAULT_IDS)
            directory = prepare_benchmark(root, base, args.run_id, numbers)
            print(json.dumps({"prepared_run": str(directory), "status": "contract_incompatible"}))
            return 0
        if args.action == "benchmark":
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{5,79}", args.run_id):
                raise ValueError("Unsafe run ID")
            print(json.dumps(_run_benchmark(base / args.run_id, root, env, transport)))
            return 0
        client = _client(env, transport)
        if args.action == "config":
            print(json.dumps({"status": "valid", "host": validate_url(env.get("QWEN_REMOTE_URL")),
                              "model": MODEL_ID, "token_present": True}))
            return 0
        if args.action == "dry-run":
            result = {"status": "offline_valid", "host": client.host, "model": MODEL_ID,
                      "network_calls": 0, "inference_calls": 0,
                      "api_contract_version": API_CONTRACT_VERSION,
                      "variant_a_contract": "contract_incompatible" if len(SYSTEM_PROMPT) > MAX_SYSTEM_PROMPT_CHARS else "compatible",
                      "variant_a_system_prompt_characters": len(SYSTEM_PROMPT),
                      "variant_b_contract": "contract_incompatible" if len(VISUAL_PROMPT) > MAX_SYSTEM_PROMPT_CHARS else "compatible",
                      "variant_b_system_prompt_characters": len(VISUAL_PROMPT)}
        elif args.action == "health":
            result = client.health()
        else:
            client.validate_generation_request(args.prompt, args.system_prompt,
                                               args.max_new_tokens)
            health_result = client.health()
            client.require_capacity(health_result, min_seconds=client.timeout + 5)
            response = client.generate(args.prompt, args.system_prompt, args.max_new_tokens)
            result = {"requested_model": MODEL_ID, "api_contract_version": API_CONTRACT_VERSION,
                      "remote_provider": "kaggle_gpu_cloudflare_quick_tunnel",
                      "submitted_prompt": args.prompt, "system_prompt": args.system_prompt,
                      "generation_parameters": {"max_new_tokens": args.max_new_tokens},
                      "executed_at_utc": _now(), "health_before": health_result,
                      "response": response}
        output = args.output or base / f"{args.action}-{uuid4().hex}.json"
        _write_new_json(output, result)
        print(json.dumps({"status": "ok", "diagnostic": str(output)}))
        return 0
    except (RemoteQwenError, ValueError, OSError, KeyError) as exc:
        if isinstance(exc, RemoteQwenError):
            print(json.dumps({"status": "error", "error": exc.as_dict()}), file=sys.stderr)
            return 2
        print(json.dumps({"status": "error", "code": "preparation_failure",
                          "message": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
