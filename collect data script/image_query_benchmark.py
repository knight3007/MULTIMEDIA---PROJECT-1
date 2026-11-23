"""Isolated, resumable Qwen query-only benchmark. No image pipeline calls."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from collector_common import PROJECT_ROOT
from query_generator import (DEFAULT_QWEN_MODEL, MAX_NEW_TOKENS, SYSTEM_PROMPT,
                             QwenQueryGenerator, QueryGenerationError, normalize_query)
from semantic_decisions import load_decisions
from validate_vocabulary import validate_sources
from vocabulary_registry import load_registry, validate_registry


SCHEMA_VERSION = 1
PROMPT_A_VERSION = "production-system-prompt-sha256"
PROMPT_B_VERSION = "sense-aware-visual-intent-v1"
BENCHMARK_IDS = [4, 9, 19, 35, 41, 42, 43, 47, 48, 49, 50, 51, 53,
                 54, 55, 61, 62, 65, 66, 67, 71, 74, 77, 82, 87]
VISUAL_TYPES = frozenset({
    "concrete_object", "food", "animal", "person_role", "place", "action",
    "emotion_state", "physical_attribute", "time_weather", "abstract_concept",
    "function_word", "educational_visual",
})
AUDIT_QUERY_PATH = Path("reports/image_pipeline_audit/20261106T102750Z-cd93f8a1/02_qwen_queries_100.json")
INPUT_PATHS = [Path("data/vocabulary") / f"{lang}.txt" for lang in ("en", "jp", "vn")]
INPUT_PATHS += [Path("data/vocabulary") / name for name in
                ("id_registry_v1.json", "semantic_decisions_v1.json", "unified_dataset_v1.json")]
INPUT_PATHS += [AUDIT_QUERY_PATH, Path("data/query/generated_qwen.json"),
                Path("data/query/generated_qwen_water_beverage.json"),
                Path("baseline/media-staging/image-queries/generated_qwen_full_v1.json"),
                Path("baseline/media-staging/image-queries/generated_qwen_sparse_v1.json")]
INPUT_PATHS += [Path("collect data script") / name for name in
                ("query_generator.py", "stage_vocabulary_images.py", "dataset_builder.py",
                 "semantic_decisions.py", "vocabulary_registry.py")]
OUTPUT_BASE = Path("reports/image_pipeline_benchmark")
REVIEW_SEED = 20261106

VISUAL_PROMPT = """You design image-search queries for a trilingual vocabulary lesson. Return exactly one JSON object with exactly these keys: visual_type, search_query, visual_description, negative_constraints, reason. No Markdown or extra text.

visual_type must be one of: concrete_object, food, animal, person_role, place, action, emotion_state, physical_attribute, time_weather, abstract_concept, function_word, educational_visual.
search_query: a concise English phrase for visible content, not a dictionary definition or a bare abstract word.
visual_description: one English sentence describing what a viewer can actually see.
negative_constraints: a JSON array of short English phrases identifying likely wrong senses or misleading imagery; use [] if none.
reason: one short English sentence connecting the depiction to the supplied meaning and noting uncertainty when the semantic decision is pending.

Use the English, Japanese, Vietnamese and any approved target sense together. An approved target sense and approved image search intent take precedence. A pending or unreviewed status does not authorize a new meaning; describe a provisional depiction and state the uncertainty in reason. Do not turn every word into an object. Show actions as a person visibly doing the action, time words as calendars or time sequences, and abstract or function words as educational visuals when a literal photo cannot express them. Avoid logos, watermarks, stock-preview text, unrelated objects and words used as brand names. Keep JSON compact and finish it within the token budget."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze_inputs(root: Path, paths: list[Path]) -> dict[str, str]:
    root = root.resolve()
    result = {}
    for path in paths:
        resolved = path.resolve()
        if not resolved.is_relative_to(root) or not resolved.is_file():
            raise ValueError(f"Missing or unsafe benchmark input: {path}")
        result[resolved.relative_to(root).as_posix()] = sha256(resolved)
    return result


def verify_hashes(root: Path, hashes: dict[str, str]) -> None:
    for name, digest in hashes.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file() or sha256(path) != digest:
            raise ValueError(f"Input hash mismatch: {name}")


def write_checkpoint(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_checkpoint(path: Path, root: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Benchmark schema version mismatch")
    verify_hashes(root, document["input_hashes"])
    return document


def resolve_effective_query(model_query: str | None, decision: dict | None) -> tuple[str | None, str]:
    if decision and decision.get("review_status") == "approved":
        intent = decision.get("image_search_intent")
        if not intent:
            raise ValueError("Approved target sense has no image search intent")
        return intent, "human_approved"
    return model_query, "model_generated_unreviewed"


def load_inputs(root: Path) -> list[dict]:
    paths = {lang: root / "data/vocabulary" / f"{lang}.txt" for lang in ("en", "jp", "vn")}
    triples, issues = validate_sources(paths)
    if issues:
        raise ValueError("Vocabulary sources invalid: " + "; ".join(issues))
    registry = load_registry(root)
    canonical_ids = validate_registry(triples, registry)
    decisions = load_decisions(root, registry)
    dataset = json.loads((root / "data/vocabulary/unified_dataset_v1.json").read_text(encoding="utf-8"))
    ledger = json.loads((root / AUDIT_QUERY_PATH).read_text(encoding="utf-8"))
    if dataset.get("schema_version") != 1 or len(dataset.get("records", [])) != len(triples):
        raise ValueError("Saved canonical dataset does not match source rows")
    by_id = {record["vocab_id"]: record for record in dataset["records"]}
    qwen_by_id = {record["vocab_id"]: record for record in ledger}
    if len(by_id) != len(triples) or len(qwen_by_id) != len(triples):
        raise ValueError("Duplicate or missing canonical dataset/Qwen ledger IDs")
    selected = []
    for number in BENCHMARK_IDS:
        vocab_id = canonical_ids[number - 1]
        english, japanese, vietnamese = triples[number - 1]
        record, historical = by_id[vocab_id], qwen_by_id[vocab_id]
        if (record["source_row_index"] != number or record["english"] != english
                or record["japanese"]["display"] != japanese
                or record["vietnamese"] != vietnamese
                or historical["english"] != english):
            raise ValueError(f"Canonical triple mismatch at source row {number}")
        approved = decisions["approved"].get(vocab_id)
        context = decisions["context"].get(vocab_id)
        expected_status = "approved" if approved else "needs_decision" if context else "unreviewed"
        if record["review_status"] != expected_status or record["target_sense"] != (
                approved["target_sense"] if approved else None):
            raise ValueError(f"Semantic decision mismatch for {vocab_id}")
        old_model_query = historical["parsed_qwen_query"]
        effective, provenance = resolve_effective_query(old_model_query, approved)
        if (historical["effective_image_query"] != effective
                or historical["query_provenance"] != provenance):
            raise ValueError(f"Historical query provenance mismatch for {vocab_id}")
        selected.append({
            "vocab_id": vocab_id, "source_row_index": number,
            "english": english, "japanese": record["japanese"], "vietnamese": vietnamese,
            "semantic_review_status": expected_status, "target_sense": record["target_sense"],
            "image_search_intent": approved.get("image_search_intent") if approved else None,
            "usage_note": record["usage_note"], "annotation_status": record["annotation_status"],
            "historical": {
                "raw_decoded_text": historical["raw_qwen_output"],
                "raw_model_query": old_model_query, "effective_search_query": effective,
                "query_provenance": provenance, "cache_status": historical["cache_status"],
                "evidence_source_file": historical["evidence_source_file"],
                "generation_method": historical.get("generation_method"),
            },
        })
    return selected


def parse_visual_output(raw: str, ended: bool) -> dict:
    result = {"raw_decoded_text": raw, "parsed": None,
              "validation_status": "invalid", "error": None}
    if not ended:
        result["error"] = "generation reached token limit without EOS"
        return result
    try:
        parsed = json.loads(raw)
        keys = {"visual_type", "search_query", "visual_description", "negative_constraints", "reason"}
        if not isinstance(parsed, dict) or set(parsed) != keys:
            raise ValueError("JSON must contain exactly the five required fields")
        if parsed["visual_type"] not in VISUAL_TYPES:
            raise ValueError("unsupported visual_type")
        for key in ("search_query", "visual_description", "reason"):
            if not isinstance(parsed[key], str) or not parsed[key].strip():
                raise ValueError(f"{key} must be nonempty text")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 ,'-]*", parsed["search_query"]):
            raise ValueError("search_query must be an English search phrase")
        negatives = parsed["negative_constraints"]
        if (not isinstance(negatives, list) or len(negatives) > 8
                or any(not isinstance(item, str) or not item.strip() for item in negatives)):
            raise ValueError("negative_constraints must be an array of at most eight nonempty strings")
    except (json.JSONDecodeError, ValueError, TypeError) as error:
        result["error"] = str(error)
    else:
        result["parsed"] = parsed
        result["validation_status"] = "valid"
    return result


class TracedQwen(QwenQueryGenerator):
    """Run the unchanged production generator logic while retaining decoded attempts."""

    def __init__(self, model_path: Path):
        super().__init__(str(model_path), batch_size=1)
        self.raw_calls = []

    def _generate_raw(self, words: list[str], *, correction: str | None = None):
        outputs = super()._generate_raw(words, correction=correction)
        self.raw_calls.extend({"word": word, "correction_prompt": correction,
                               "raw_decoded_text": raw, "ended_with_eos": ended}
                              for word, (raw, ended) in zip(words, outputs))
        return outputs


class QwenBackend:
    def __init__(self):
        os.environ["HF_HUB_OFFLINE"] = "1"
        cache = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
        snapshots = cache / "hub/models--Qwen--Qwen3-1.7B/snapshots"
        candidates = [path for path in snapshots.glob("*") if (path / "config.json").is_file()
                      and (path / "model.safetensors.index.json").is_file()]
        if len(candidates) != 1:
            raise ValueError("Expected exactly one complete local Qwen model snapshot")
        self.generator = TracedQwen(candidates[0])
        self.metadata = {"model": DEFAULT_QWEN_MODEL, "revision": candidates[0].name,
                         "device": None, "dtype": None}

    def _load(self):
        self.generator._load()
        self.metadata["device"] = str(self.generator._input_device())
        self.metadata["dtype"] = str(self.generator.model.dtype)
        self.metadata["torch_version"] = self.generator.torch.__version__
        import transformers
        self.metadata["transformers_version"] = transformers.__version__
        self.metadata["tokenizer_padding_side"] = self.generator.tokenizer.padding_side
        self.metadata["tokenizer_pad_token_id"] = self.generator.tokenizer.pad_token_id
        self.metadata["tokenizer_eos_token_id"] = self.generator.tokenizer.eos_token_id
        self.metadata["model_eos_token_id"] = self.generator.model.generation_config.eos_token_id

    def generate(self, variant: str, row: dict) -> dict:
        started = time.perf_counter()
        self._load()
        if variant == "a":
            self.generator.raw_calls = []
            try:
                query = self.generator._generate_chunk([row["english"]])[0]
                error = None
            except Exception as exc:
                query, error = None, str(exc)
            attempts = list(self.generator.raw_calls)
            final = attempts[-1] if attempts else {}
            return {"raw_decoded_text": final.get("raw_decoded_text"),
                    "raw_attempts": attempts, "parsed_query": query,
                    "validation_status": "valid" if query is not None else "invalid",
                    "error": error, "ended_with_eos": final.get("ended_with_eos"),
                    "duration_seconds": round(time.perf_counter() - started, 3)}
        if variant != "b":
            raise ValueError(f"Unknown variant: {variant}")
        tokenizer, model, torch = (self.generator.tokenizer, self.generator.model,
                                   self.generator.torch)
        context = {key: row[key] for key in
                   ("english", "japanese", "vietnamese", "semantic_review_status",
                    "target_sense", "image_search_intent", "usage_note")}
        user = "Vocabulary record (JSON): " + json.dumps(context, ensure_ascii=False)
        prompt = tokenizer.apply_chat_template(
            [{"role": "system", "content": VISUAL_PROMPT}, {"role": "user", "content": user}],
            tokenize=False, add_generation_prompt=True, enable_thinking=False)
        inputs = tokenizer([prompt], return_tensors="pt", padding=True, add_special_tokens=False)
        device = self.generator._input_device()
        inputs = {name: tensor.to(device) for name, tensor in inputs.items()}
        eos_ids = model.generation_config.eos_token_id or tokenizer.eos_token_id
        if isinstance(eos_ids, int):
            eos_ids = [eos_ids]
        with torch.inference_mode():
            output = model.generate(**inputs, max_new_tokens=256, do_sample=False,
                                    pad_token_id=tokenizer.pad_token_id, eos_token_id=eos_ids)
        tokens = output[0, inputs["input_ids"].shape[1]:].cpu().tolist()
        raw = tokenizer.decode(tokens, skip_special_tokens=True)
        ended = any(token in set(eos_ids) for token in tokens)
        result = parse_visual_output(raw, ended)
        return {**result, "ended_with_eos": ended,
                "duration_seconds": round(time.perf_counter() - started, 3)}

    def close(self):
        self.generator.close()


def protected_paths(root: Path) -> list[Path]:
    directories = [root / "data/vocabulary", root / "data/query", root / "data/image",
                   root / "data/audio", root / "baseline"]
    return sorted(path for directory in directories if directory.exists()
                  for path in directory.rglob("*") if path.is_file()
                  and "__pycache__" not in path.parts)


def _write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _build_review(run_dir: Path, rows: list[dict]) -> None:
    review_path, mapping_path = run_dir / "owner_review.csv", run_dir / "blind_mapping.json"
    if review_path.exists() or mapping_path.exists():
        if review_path.exists() and mapping_path.exists():
            return  # A resumed run must not erase human labels.
        raise ValueError("Incomplete owner review packet; preserve the existing file")
    candidates = []
    for row in rows:
        for variant, query in (
                ("historical_current", row["historical"]["effective_search_query"]),
                ("fresh_a", row["variant_a"]["parsed_query"]),
                ("fresh_b", row["variant_b"]["parsed_query"])):
            candidates.append((row, variant, query))
    random.Random(REVIEW_SEED).shuffle(candidates)
    review_rows, mapping = [], []
    for index, (row, variant, query) in enumerate(candidates, 1):
        review_id = f"Q{index:03d}"
        review_rows.append({
            "review_id": review_id, "source_row_index": row["source_row_index"],
            "english": row["english"], "japanese": row["japanese"]["display"],
            "vietnamese": row["vietnamese"], "semantic_review_status": row["semantic_review_status"],
            "approved_target_sense": row["target_sense"] or "", "usage_note": row["usage_note"] or "",
            "candidate_query": query or "", "candidate_available": bool(query),
            "correct_intended_meaning": "", "visibly_depictable": "",
            "ambiguous_or_wrong_sense": "", "inappropriate_text_or_brand_lure": "",
            "reviewer_rationale": "", "reviewer_id": "", "reviewed_at": "",
        })
        mapping.append({"review_id": review_id, "vocab_id": row["vocab_id"],
                        "source_row_index": row["source_row_index"], "variant": variant})
    _write_csv(review_path, list(review_rows[0]), review_rows)
    write_checkpoint(mapping_path, {
        "schema_version": SCHEMA_VERSION, "seed": REVIEW_SEED, "mapping": mapping})


def _build_csv(run_dir: Path, rows: list[dict]) -> None:
    flat = []
    for row in rows:
        a, b, old = row["variant_a"], row["variant_b"], row["historical"]
        flat.append({
            "source_row_index": row["source_row_index"], "vocab_id": row["vocab_id"],
            "english": row["english"], "japanese": row["japanese"]["display"],
            "vietnamese": row["vietnamese"], "semantic_review_status": row["semantic_review_status"],
            "target_sense": row["target_sense"] or "", "usage_note": row["usage_note"] or "",
            "historical_raw_model_query": old["raw_model_query"],
            "historical_effective_search_query": old["effective_search_query"],
            "historical_query_provenance": old["query_provenance"],
            "variant_a_raw_decoded_text": a["raw_decoded_text"] or "",
            "variant_a_raw_model_query": a["parsed_query"] or "",
            "variant_a_effective_search_query": a["effective_search_query"] or "",
            "variant_a_status": a["validation_status"], "variant_a_error": a["error"] or "",
            "variant_b_raw_decoded_text": b["raw_decoded_text"] or "",
            "variant_b_visual_type": b["parsed"]["visual_type"] if b["parsed"] else "",
            "variant_b_raw_model_query": b["parsed_query"] or "",
            "variant_b_effective_search_query": b["effective_search_query"] or "",
            "variant_b_status": b["validation_status"], "variant_b_error": b["error"] or "",
        })
    _write_csv(run_dir / "query_experiment.csv", list(flat[0]), flat)


def validate_experiment_document(document: dict) -> None:
    """Validate the versioned 25-row persistence contract before publication."""
    if document.get("schema_version") != SCHEMA_VERSION or not isinstance(document.get("input_hashes"), dict):
        raise ValueError("Invalid benchmark schema version or input hashes")
    rows = document.get("records")
    if not isinstance(rows, list) or [r.get("source_row_index") for r in rows] != BENCHMARK_IDS:
        raise ValueError("Experiment must contain exactly the 25 canonical source rows")
    for row in rows:
        if row.get("vocab_id") is None or row.get("semantic_review_status") not in {
                "approved", "needs_decision", "unreviewed"}:
            raise ValueError("Invalid row identity or semantic status")
        if row["semantic_review_status"] != "approved" and row.get("target_sense") is not None:
            raise ValueError("Pending/unreviewed row has an approved target sense")
        decision = {"review_status": row["semantic_review_status"],
                    "image_search_intent": row.get("image_search_intent")}
        old = row["historical"]
        old_effective, old_provenance = resolve_effective_query(old["raw_model_query"], decision)
        if (old["effective_search_query"], old["query_provenance"]) != (
                old_effective, old_provenance):
            raise ValueError("Historical model query and effective query are conflated")
        for variant in ("a", "b"):
            result = row[f"variant_{variant}"]
            if result.get("validation_status") not in {"valid", "invalid"}:
                raise ValueError("Invalid generation status")
            query = result.get("parsed_query")
            if result["validation_status"] == "valid":
                if not isinstance(result.get("raw_decoded_text"), str):
                    raise ValueError("Valid generation lacks decoded raw text")
                expected = (normalize_query(result["raw_decoded_text"]) if variant == "a" else
                            parse_visual_output(result["raw_decoded_text"], result["ended_with_eos"])["parsed"])
                if variant == "b":
                    if expected != result.get("parsed"):
                        raise ValueError("Structured JSON parse differs from raw output")
                    expected = expected["search_query"]
                if query != expected:
                    raise ValueError("Parsed query differs from raw output")
            elif query is not None or not result.get("error"):
                raise ValueError("Invalid generation has query or lacks error")
            effective, provenance = resolve_effective_query(query, decision)
            if query is None:
                effective, provenance = None, None
            if (result.get("effective_search_query"), result.get("query_provenance")) != (
                    effective, provenance):
                raise ValueError("Model query and effective query are conflated")


def run_experiment(root: Path, run_id: str, *, resume: bool = False,
                   output_base: Path | None = None, backend=None,
                   protected_paths: list[Path] | None = None) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Unsafe benchmark run ID")
    root = root.resolve()
    wall_started = time.perf_counter()
    base = output_base or root / OUTPUT_BASE
    run_dir = base / run_id
    rows = load_inputs(root)
    hashes = freeze_inputs(root, [root / path for path in INPUT_PATHS])
    protected = freeze_inputs(root, protected_paths if protected_paths is not None
                              else globals()["protected_paths"](root))
    manifest_path = run_dir / "experiment_manifest.json"
    if resume:
        manifest = read_checkpoint(manifest_path, root)
        if (manifest.get("run_id") != run_id or manifest.get("protected_hashes") != protected
                or manifest.get("input_hashes") != hashes):
            raise ValueError("Resume hash or run identity mismatch")
        prompts = json.loads((run_dir / "prompts.json").read_text(encoding="utf-8"))
        if (prompts["variant_a"]["system_prompt"] != SYSTEM_PROMPT
                or prompts["variant_a"]["user_template"] != "Input: {english}\nQuery:"
                or prompts["variant_b"]["system_prompt"] != VISUAL_PROMPT
                or manifest["prompt_versions"]["b"] != PROMPT_B_VERSION
                or manifest["settings"]["a"]["max_new_tokens"] != MAX_NEW_TOKENS
                or manifest["settings"]["b"]["max_new_tokens"] != 256):
            raise ValueError("Resume prompt or generation settings mismatch")
    else:
        run_dir.mkdir(parents=True, exist_ok=False)
        shutil.copyfile(root / OUTPUT_BASE / "README.md", run_dir / "README.md")
        manifest = {
            "schema_version": SCHEMA_VERSION, "run_id": run_id,
            "purpose": "isolated_query_only_benchmark", "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "git_head_at_start": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
            "source_row_ids": BENCHMARK_IDS,
            "input_hashes": hashes, "protected_hashes": protected,
            "prompt_versions": {"a": PROMPT_A_VERSION + ":" + hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
                                "b": PROMPT_B_VERSION},
            "settings": {"model": DEFAULT_QWEN_MODEL, "a": {"max_new_tokens": MAX_NEW_TOKENS,
                         "batch_size": 1, "do_sample": False, "enable_thinking": False,
                         "decode_skip_special_tokens": True, "retry_invalid_once": True},
                         "b": {"max_new_tokens": 256, "batch_size": 1, "do_sample": False,
                         "enable_thinking": False, "decode_skip_special_tokens": True}},
            "review_seed": REVIEW_SEED, "status": "running", "model_runtime": None,
            "failure_summaries": {}, "generation_duration_seconds": {},
        }
        write_checkpoint(manifest_path, manifest)
        write_checkpoint(run_dir / "prompts.json", {
            "schema_version": SCHEMA_VERSION,
            "variant_a": {"version": manifest["prompt_versions"]["a"],
                          "system_prompt": SYSTEM_PROMPT,
                          "user_template": "Input: {english}\nQuery:",
                          "retry_behavior": "query_generator.QwenQueryGenerator._generate_chunk"},
            "variant_b": {"version": PROMPT_B_VERSION, "system_prompt": VISUAL_PROMPT,
                          "user_template": "Vocabulary record (JSON): {english,japanese,vietnamese,semantic_review_status,target_sense,image_search_intent,usage_note}"},
        })
        write_checkpoint(run_dir / "protected_hashes_before.json", {
            "schema_version": SCHEMA_VERSION, "sha256": protected})
    if backend is None:
        backend = QwenBackend()
    try:
        for variant in ("a", "b"):
            output_dir = run_dir / "raw_generation" / f"variant_{variant}"
            output_dir.mkdir(parents=True, exist_ok=True)
            for row in rows:
                number = row["source_row_index"]
                path = output_dir / f"{number:03d}.json"
                if path.exists():
                    saved = json.loads(path.read_text(encoding="utf-8"))
                    if saved.get("vocab_id") != row["vocab_id"] or saved.get("variant") != variant:
                        raise ValueError(f"Existing raw evidence mismatch: {path}")
                    continue
                started = time.perf_counter()
                try:
                    result = backend.generate(variant, row)
                except Exception as error:
                    result = {"raw_decoded_text": None, "raw_attempts": [], "parsed": None,
                              "parsed_query": None, "validation_status": "invalid",
                              "error": f"{type(error).__name__}: {error}", "ended_with_eos": None,
                              "duration_seconds": round(time.perf_counter() - started, 3)}
                write_checkpoint(path, {"schema_version": SCHEMA_VERSION, "variant": variant,
                                        "vocab_id": row["vocab_id"], **result})
                print(f"[{variant.upper()}] {number:03d} {row['english']}: {result['validation_status']}", flush=True)
    finally:
        if manifest.get("model_runtime") is None or backend.metadata.get("device") is not None:
            manifest["model_runtime"] = backend.metadata
        backend.close()
        write_checkpoint(manifest_path, manifest)

    complete = []
    failure_summaries = {}
    generation_duration = {}
    for row in rows:
        entry = dict(row)
        decision = {"review_status": row["semantic_review_status"],
                    "image_search_intent": row["image_search_intent"]}
        for variant in ("a", "b"):
            result = json.loads((run_dir / "raw_generation" / f"variant_{variant}" /
                                 f"{row['source_row_index']:03d}.json").read_text(encoding="utf-8"))
            query = result.get("parsed_query") if variant == "a" else (
                result["parsed"]["search_query"] if result.get("parsed") else None)
            result["parsed_query"] = query
            effective, provenance = resolve_effective_query(query, decision)
            result["effective_search_query"] = effective if query is not None else None
            result["query_provenance"] = provenance if query is not None else None
            entry[f"variant_{variant}"] = result
            generation_duration[variant] = generation_duration.get(variant, 0) + result["duration_seconds"]
            if result["validation_status"] != "valid":
                failures = failure_summaries.setdefault(variant, [])
                failures.append({"source_row_index": row["source_row_index"], "error": result["error"]})
        complete.append(entry)
    verify_hashes(root, hashes)
    verify_hashes(root, protected)
    document = {"schema_version": SCHEMA_VERSION, "run_id": run_id, "input_hashes": hashes,
                "records": complete}
    validate_experiment_document(document)
    write_checkpoint(run_dir / "query_experiment.json", document)
    _build_csv(run_dir, complete)
    _build_review(run_dir, complete)
    manifest.update(status="complete", failure_summaries=failure_summaries,
                    generation_duration_seconds={key: round(value, 3) for key, value in generation_duration.items()},
                    protected_hash_verification="identical")
    if "completed_at_utc" not in manifest:
        manifest["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
        manifest["run_wall_seconds"] = round(time.perf_counter() - wall_started, 3)
    write_checkpoint(manifest_path, manifest)
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") +
                        "-" + uuid4().hex[:8])
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    result = run_experiment(PROJECT_ROOT, args.run_id, resume=args.resume)
    print(f"Benchmark: {PROJECT_ROOT / OUTPUT_BASE / args.run_id}")
    return 0 if all(row[v]["validation_status"] == "valid" for row in result["records"]
                    for v in ("variant_a", "variant_b")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
