"""Isolated ten-request Qwen3-4B V4 comparison; preparation is offline."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
import time
from pathlib import Path

from image_query_benchmark import (VISUAL_PROMPT, load_inputs,
                                   validate_experiment_document, verify_hashes)
from query_generator import SYSTEM_PROMPT, QueryGenerationError, normalize_query
from remote_qwen_client import (API_CONTRACT_VERSION, MODEL_ID, RemoteQwenClient,
                                RemoteQwenError)
from remote_qwen_probe import (_client, _now, _user_prompt, _write_new_json,
                               validate_visual_text, INPUT_FILES, SOURCE_EXPERIMENT)


V4_IDS = (4, 9, 41, 54, 65)
PROMPT_SNAPSHOT = Path("reports/image_pipeline_benchmark/20261106-image-query-v1/prompts.json")
D0_MANIFEST = Path("reports/remote_qwen/d0-five-20261107/experiment_manifest.json")
RUN_ID = "d1-five-20261107-qwen4b-v4"
REVIEW_SEED = 20261107


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source(root: Path) -> tuple[dict, dict, dict[int, dict]]:
    prompts = json.loads((root / PROMPT_SNAPSHOT).read_text(encoding="utf-8"))
    if (prompts["variant_a"]["system_prompt"] != SYSTEM_PROMPT or
            prompts["variant_b"]["system_prompt"] != VISUAL_PROMPT):
        raise ValueError("Frozen prompts differ from original implementation")
    experiment = json.loads((root / SOURCE_EXPERIMENT).read_text(encoding="utf-8"))
    verify_hashes(root, experiment["input_hashes"])
    validate_experiment_document(experiment)
    canonical = {row["source_row_index"]: row for row in load_inputs(root)}
    historical = {row["source_row_index"]: row for row in experiment["records"]}
    for number in V4_IDS:
        if canonical[number]["vocab_id"] != historical[number]["vocab_id"]:
            raise ValueError("Canonical and historical vocabulary IDs differ")
    return prompts, canonical, historical


def prepare_v4_benchmark(root: Path, output_base: Path, run_id: str = RUN_ID) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{5,79}", run_id):
        raise ValueError("Unsafe run ID")
    root = root.resolve()
    prompts, canonical, historical = _source(root)
    requests = []
    for number in V4_IDS:
        row, prior = canonical[number], historical[number]
        for variant in ("a", "b"):
            prompt = prompts[f"variant_{variant}"]
            system = prompt["system_prompt"]
            user = (prompt["user_template"].format(english=row["english"])
                    if variant == "a" else _user_prompt(row))
            max_tokens = 32 if variant == "a" else 256
            RemoteQwenClient.validate_generation_request(user, system, max_tokens)
            requests.append({
                "request_id": f"{number:03d}-{variant}",
                "source_row_index": number, "vocab_id": row["vocab_id"],
                "english": row["english"], "japanese": row["japanese"],
                "vietnamese": row["vietnamese"],
                "semantic_review_status": row["semantic_review_status"],
                "approved_target_sense": row["target_sense"],
                "approved_image_search_intent": row["image_search_intent"],
                "usage_note": row["usage_note"],
                "variant": variant, "prompt_version": prompt["version"],
                "system_prompt": system, "system_prompt_sha256": _sha(system),
                "user_prompt": user, "user_prompt_sha256": _sha(user),
                "max_new_tokens": max_tokens,
                "generation_parameters": {"do_sample": False, "enable_thinking": False,
                                          "max_new_tokens": max_tokens},
                "requested_model": MODEL_ID,
                "local_1_7b_result": prior[f"variant_{variant}"],
                "historical_1_7b_result": prior["historical"],
                "response_status": "not_run", "response_text": None,
                "model_revision": None, "model_revision_status": "unverified",
                "eos_status": "unavailable", "finish_reason": "unavailable",
            })
    input_files = (*INPUT_FILES, D0_MANIFEST)
    hashes = {path.as_posix(): hashlib.sha256((root / path).read_bytes()).hexdigest()
              for path in input_files}
    run_dir = output_base / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    _write_new_json(run_dir / "experiment_manifest.json", {
        "schema_version": 2, "run_id": run_id, "status": "prepared",
        "prepared_at_utc": _now(), "api_contract_version": API_CONTRACT_VERSION,
        "remote_provider": "kaggle_gpu_cloudflare_quick_tunnel",
        "requested_model": MODEL_ID, "model_revision": None,
        "model_revision_status": "unverified", "expected_generation_calls": len(requests),
        "input_hashes": hashes, "requests": requests,
    })
    _write_review_template(run_dir, canonical, historical)
    (run_dir / "README.md").write_text(
        "# D1 Qwen3-4B V4 five-word benchmark\n\n"
        "Prepared only; no remote calls have occurred. The manifest freezes ten exact "
        "requests for rows 004, 009, 041, 054 and 065. Run through the explicit "
        "`benchmark-v4 --live` command documented in `docs/REMOTE_QWEN_API_V2.md`. "
        "Give reviewers `review_ready.csv` after execution, withholding "
        "`blind_mapping.json` until labels are complete.\n", encoding="utf-8")
    return run_dir


def _write_review_template(run_dir: Path, canonical: dict, historical: dict) -> None:
    candidates = []
    for number in V4_IDS:
        row, prior = canonical[number], historical[number]
        for variant, query in (
                ("historical_current_1_7b", prior["historical"]["effective_search_query"]),
                ("local_a_1_7b", prior["variant_a"]["parsed_query"]),
                ("local_b_1_7b", prior["variant_b"]["parsed_query"]),
                ("remote_a_4b", None), ("remote_b_4b", None)):
            candidates.append((row, variant, query))
    random.Random(REVIEW_SEED).shuffle(candidates)
    mapping = []
    columns = ("review_id", "vocab_id", "english", "japanese", "vietnamese",
               "candidate_query", "candidate_available", "correct_intended_meaning",
               "visibly_depictable", "ambiguous_or_wrong_sense", "reviewer_rationale",
               "reviewer_id", "reviewed_at")
    with (run_dir / "review_template.csv").open("x", encoding="utf-8", newline="") as handle:
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
    _write_new_json(run_dir / "blind_mapping.json", {
        "schema_version": 2, "seed": REVIEW_SEED, "mapping": mapping})


def _check_capacity(health: dict, remaining: int, timeout: float) -> None:
    if (health["remaining_generations"] < remaining or
            health["remaining_seconds"] < remaining * (timeout + 5)):
        raise RemoteQwenError("insufficient_quota",
                              "Insufficient quota or session time for remaining benchmark calls")


def _validate_manifest(root: Path, run_dir: Path, manifest: dict) -> list[dict]:
    if (manifest.get("schema_version") != 2 or manifest.get("run_id") != run_dir.name
            or manifest.get("api_contract_version") != API_CONTRACT_VERSION
            or manifest.get("requested_model") != MODEL_ID):
        raise ValueError("Invalid V4 benchmark manifest")
    verify_hashes(root, manifest["input_hashes"])
    requests = manifest.get("requests")
    expected = [(n, v) for n in V4_IDS for v in ("a", "b")]
    if (not isinstance(requests, list) or len(requests) != 10 or
            [(r.get("source_row_index"), r.get("variant")) for r in requests] != expected):
        raise ValueError("V4 benchmark must contain the exact ten requests")
    prompts, canonical, historical = _source(root)
    for request in requests:
        number = request["source_row_index"]
        row = canonical[number]
        prior = historical[number]
        prompt = prompts[f"variant_{request['variant']}"]
        user = (prompt["user_template"].format(english=row["english"])
                if request["variant"] == "a" else _user_prompt(row))
        max_tokens = 32 if request["variant"] == "a" else 256
        if (request["request_id"] != f"{number:03d}-{request['variant']}" or
                request["vocab_id"] != row["vocab_id"] or
                request["english"] != row["english"] or
                request["japanese"] != row["japanese"] or
                request["vietnamese"] != row["vietnamese"] or
                request["approved_target_sense"] != row["target_sense"] or
                request["requested_model"] != MODEL_ID or
                request["system_prompt"] != prompt["system_prompt"] or
                request["user_prompt"] != user or
                request["prompt_version"] != prompt["version"] or
                request["system_prompt_sha256"] != _sha(prompt["system_prompt"]) or
                request["user_prompt_sha256"] != _sha(user) or
                request["max_new_tokens"] != max_tokens or
                request["generation_parameters"] != {
                    "do_sample": False, "enable_thinking": False,
                    "max_new_tokens": max_tokens} or
                request["local_1_7b_result"] != prior[f"variant_{request['variant']}"] or
                request["historical_1_7b_result"] != prior["historical"]):
            raise ValueError("V4 manifest prompt or vocabulary identity changed")
        RemoteQwenClient.validate_generation_request(user, prompt["system_prompt"], max_tokens)
    return requests


def run_v4_benchmark(root: Path, run_dir: Path, environ: dict, transport=None) -> dict:
    root = root.resolve()
    run_dir = run_dir.resolve()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{5,79}", run_dir.name):
        raise ValueError("Unsafe run ID")
    if (run_dir / "remote_generation").exists() or (run_dir / "execution_summary.json").exists():
        raise ValueError("Run already has generation evidence; create a new run")
    manifest = json.loads((run_dir / "experiment_manifest.json").read_text(encoding="utf-8"))
    requests = _validate_manifest(root, run_dir, manifest)
    client = _client(environ, transport)
    started = time.perf_counter()
    first_health = client.health()
    _check_capacity(first_health, len(requests), client.timeout)
    (run_dir / "remote_generation").mkdir()
    results = []
    generation_calls = 0
    for index, request in enumerate(requests):
        evidence = {key: request[key] for key in
                    ("request_id", "source_row_index", "vocab_id", "english", "japanese",
                     "vietnamese", "semantic_review_status", "approved_target_sense",
                     "variant", "prompt_version", "system_prompt", "system_prompt_sha256",
                     "user_prompt", "user_prompt_sha256", "generation_parameters",
                     "requested_model")}
        evidence.update({"api_contract_version": API_CONTRACT_VERSION,
                         "remote_provider": manifest["remote_provider"],
                         "returned_model": None, "model_revision": None,
                         "model_revision_status": "unverified", "eos_status": "unavailable",
                         "finish_reason": "unavailable", "response_text": None,
                         "input_tokens": None, "output_tokens": None,
                         "request_status": "not_started", "parse_status": "not_available",
                         "validation_errors": [], "executed_at_utc": _now()})
        try:
            health = first_health if index == 0 else client.health()
            _check_capacity(health, len(requests) - index, client.timeout)
            evidence["remaining_generations_before"] = health["remaining_generations"]
            evidence["remaining_seconds_before"] = health["remaining_seconds"]
            evidence["health_round_trip_seconds"] = health["round_trip_seconds"]
            generation_calls += 1
            response = client.generate(request["user_prompt"], request["system_prompt"],
                                       request["max_new_tokens"])
            evidence.update({"request_status": "success", "returned_model": response["model"],
                             "response_text": response["text"],
                             "input_tokens": response["input_tokens"],
                             "output_tokens": response["output_tokens"],
                             "request_duration_seconds": response["round_trip_seconds"],
                             "server_elapsed_seconds": response["elapsed_seconds"],
                             "approx_output_tokens_per_second": response["approx_output_tokens_per_second"]})
            if request["variant"] == "a":
                try:
                    evidence["parsed_query"] = normalize_query(response["text"])
                    evidence["parse_status"] = "valid"
                except QueryGenerationError as exc:
                    evidence["parse_status"] = "invalid"
                    evidence["validation_errors"] = [str(exc)]
            else:
                parsed = validate_visual_text(response["text"])
                evidence["parse_status"] = parsed["parse_status"]
                evidence["parsed"] = parsed["parsed"]
                evidence["parsed_query"] = (parsed["parsed"] or {}).get("search_query")
                evidence["validation_errors"] = parsed["validation_errors"]
        except RemoteQwenError as exc:
            evidence.update({"request_status": "failed", "error": exc.as_dict(),
                             "request_duration_seconds": exc.round_trip_seconds})
        _write_new_json(run_dir / "remote_generation" / f"{request['request_id']}.json", evidence)
        results.append(evidence)
        if evidence["request_status"] == "failed":
            break
    summary = {"schema_version": 2, "run_id": manifest["run_id"],
               "api_contract_version": API_CONTRACT_VERSION, "requested_model": MODEL_ID,
               "completed_at_utc": _now(), "total_wall_seconds": round(time.perf_counter() - started, 6),
               "planned_generation_calls": len(requests), "generation_calls": generation_calls,
               "successful_requests": sum(r["request_status"] == "success" for r in results),
               "failed_requests": sum(r["request_status"] == "failed" for r in results),
               "invalid_outputs": sum(r["parse_status"] == "invalid" for r in results),
               "status": "complete" if len(results) == len(requests) and
               all(r["request_status"] == "success" for r in results) else "partial"}
    _write_new_json(run_dir / "execution_summary.json", summary)
    _write_review_ready(run_dir, results)
    return summary


def _write_review_ready(run_dir: Path, results: list[dict]) -> None:
    mapping = {row["review_id"]: row for row in
               json.loads((run_dir / "blind_mapping.json").read_text(encoding="utf-8"))["mapping"]}
    remote = {(row["vocab_id"], row["variant"]): row for row in results}
    with (run_dir / "review_template.csv").open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        with (run_dir / "review_ready.csv").open("x", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=reader.fieldnames)
            writer.writeheader()
            for item in reader:
                variant = mapping[item["review_id"]]["variant"]
                if variant.startswith("remote_"):
                    result = remote.get((item["vocab_id"], variant[-1]), {})
                    item["candidate_query"] = result.get("parsed_query") or ""
                    item["candidate_available"] = str(bool(item["candidate_query"]))
                writer.writerow(item)
