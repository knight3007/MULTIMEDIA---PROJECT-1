"""Phase C0: isolated candidate retention with a human-gated live adapter.

The default execution is an offline plan. No production collector paths are written.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
import ipaddress
import json
import os
import re
import shutil
import socket
import ssl
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from collector_common import PROJECT_ROOT, CollectionError
from imagecollector import (DDG_REGION, DDG_SAFESEARCH, MAX_IMAGE_BYTES, USER_AGENT,
                            normalize_image_to_jpeg, normalize_remote_url,
                            validate_image_bytes)
from image_query_benchmark import (BENCHMARK_IDS, load_inputs,
                                   validate_experiment_document, verify_hashes)


SCHEMA_VERSION = 1
SOURCE_RUN = Path("reports/image_pipeline_benchmark/20261106-image-query-v1")
OUTPUT_BASE = Path("reports/image_pipeline_benchmark")
VARIANTS = ("historical_current", "fresh_a", "fresh_b")
RETRIEVAL_VARIANT = "fresh_b"
REVIEW_COLUMNS = ("correct_intended_meaning", "visibly_depictable",
                  "ambiguous_or_wrong_sense", "inappropriate_text_or_brand_lure")
LAYOUT = ("input_snapshot", "retrieval_results", "candidates",
          "candidate_metadata", "evaluation", "manifests")
RUN_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{5,79}$")


class CandidateIntegrityError(ValueError):
    """An existing run-owned file must be inspected rather than replaced."""


class HTTPStatusError(ValueError):
    def __init__(self, status: int):
        self.status = status
        super().__init__(f"HTTP {status}; redirects are disabled")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def verify_frozen(root: Path, hashes: dict[str, str]) -> None:
    verify_hashes(root, hashes)


def json_save(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2, default=str) + "\n",
                             encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load_phase_ab(root: Path, source: Path) -> tuple[list[dict], dict]:
    """Check the completed experiment against frozen sources and canonical rows."""
    experiment = json.loads((source / "query_experiment.json").read_text(encoding="utf-8"))
    manifest = json.loads((source / "experiment_manifest.json").read_text(encoding="utf-8"))
    validate_experiment_document(experiment)
    if (manifest.get("status") != "complete" or manifest.get("schema_version") != 1
            or experiment["run_id"] != manifest.get("run_id")
            or experiment["input_hashes"] != manifest.get("input_hashes")
            or manifest.get("source_row_ids") != BENCHMARK_IDS):
        raise ValueError("Phase A/B experiment and manifest disagree")
    verify_frozen(root, manifest["input_hashes"])
    verify_frozen(root, manifest["protected_hashes"])
    canonical = load_inputs(root)
    rows = experiment["records"]
    for actual, expected in zip(rows, canonical, strict=True):
        for field in ("vocab_id", "source_row_index", "english", "japanese", "vietnamese",
                      "semantic_review_status", "target_sense", "image_search_intent", "historical"):
            if actual.get(field) != expected.get(field):
                raise ValueError(f"Phase A/B canonical mismatch: {actual.get('vocab_id')} {field}")
    _validate_blind_package(source, rows, manifest["review_seed"])
    return rows, manifest


def _validate_blind_package(source: Path, records: list[dict], seed: int) -> None:
    with (source / "owner_review.csv").open(encoding="utf-8-sig", newline="") as file:
        review_rows = list(csv.DictReader(file))
    mapping = json.loads((source / "blind_mapping.json").read_text(encoding="utf-8"))
    entries = mapping.get("mapping")
    if (mapping.get("schema_version") != 1 or mapping.get("seed") != seed
            or not isinstance(entries, list) or len(entries) != 75 or len(review_rows) != 75):
        raise ValueError("Phase A/B blind review package is incomplete")
    by_review_id = {item.get("review_id"): item for item in review_rows}
    by_vocab_id = {item["vocab_id"]: item for item in records}
    if len(by_review_id) != 75 or len(by_vocab_id) != 25:
        raise ValueError("Phase A/B blind review IDs are duplicated")
    seen = set()
    for entry in entries:
        review_id, vocab_id, variant = (entry.get("review_id"), entry.get("vocab_id"),
                                        entry.get("variant"))
        if (review_id not in by_review_id or vocab_id not in by_vocab_id
                or variant not in VARIANTS or (vocab_id, variant) in seen):
            raise ValueError("Phase A/B blind mapping is inconsistent")
        seen.add((vocab_id, variant))
        row, review = by_vocab_id[vocab_id], by_review_id[review_id]
        query = query_contract(row, variant)
        expected_query = (query["effective_search_query"] if variant == "historical_current"
                          else query["parsed_query"]) or ""
        if (entry.get("source_row_index") != row["source_row_index"]
                or review["source_row_index"] != str(row["source_row_index"])
                or review["english"] != row["english"]
                or review["japanese"] != row["japanese"]["display"]
                or review["vietnamese"] != row["vietnamese"]
                or review["semantic_review_status"] != row["semantic_review_status"]
                or review["approved_target_sense"] != (row["target_sense"] or "")
                or review["candidate_query"] != expected_query
                or review["candidate_available"] != str(bool(expected_query))
                or any(review.get(field, "") for field in (*REVIEW_COLUMNS, "reviewer_rationale",
                                                           "reviewer_id", "reviewed_at"))):
            raise ValueError(f"Phase A/B blind review differs from experiment: {review_id}")


def query_contract(row: dict, variant: str) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"unsupported query variant: {variant}")
    if variant == "historical_current":
        source = row["historical"]
        parsed = source["raw_model_query"]
        status = "valid" if parsed else "invalid"
        visual = {}
        raw = source["raw_decoded_text"]
        version = "historical_cache"
    else:
        source = row["variant_a" if variant == "fresh_a" else "variant_b"]
        if "parsed_query" not in source:
            raise ValueError("query record lacks parsed_query")
        parsed = source["parsed_query"]
        status = source["validation_status"]
        visual = source.get("parsed") or {}
        raw = source["raw_decoded_text"]
        version = "production-system-prompt-sha256" if variant == "fresh_a" else "sense-aware-visual-intent-v1"
    if status not in {"valid", "invalid"}:
        raise ValueError("malformed query validation status")
    if status == "valid" and (not isinstance(parsed, str) or not parsed.strip()):
        raise ValueError("valid query has no parsed text")
    if status == "invalid" and parsed is not None:
        raise ValueError("invalid query has parsed text")
    effective = source["effective_search_query"]
    if status == "valid" and (not isinstance(effective, str) or not effective.strip()):
        raise ValueError("valid query has no effective search text")
    return {"raw_decoded_text": raw, "parsed_query": parsed,
            "effective_search_query": effective, "query_provenance": source.get("query_provenance"),
            "query_version": version, "visual_type": visual.get("visual_type"),
            "visual_description": visual.get("visual_description"),
            "negative_constraints": visual.get("negative_constraints", []),
            "skip_reason": None if status == "valid" else "invalid_query_generation"}


def load_review_labels(path: Path, source: Path, records: list[dict] | None = None) -> dict:
    """Validate a separately completed copy of the blind owner review CSV."""
    original = source / "owner_review.csv"
    if path.resolve() == original.resolve():
        raise ValueError("human review must be a separate completed file")
    with original.open(encoding="utf-8-sig", newline="") as file:
        originals = {r["review_id"]: r for r in csv.DictReader(file)}
    with path.open(encoding="utf-8-sig", newline="") as file:
        reviewed = list(csv.DictReader(file))
    mapping = json.loads((source / "blind_mapping.json").read_text(encoding="utf-8"))
    if mapping.get("schema_version") != 1 or len(mapping.get("mapping", [])) != 75:
        raise ValueError("invalid blind review mapping")
    if len(reviewed) != len(originals) or {r.get("review_id") for r in reviewed} != set(originals):
        raise ValueError("human review must contain every blind review ID exactly once")
    by_id = {}
    for review in reviewed:
        review_id = review["review_id"]
        baseline = originals[review_id]
        for field in ("source_row_index", "english", "japanese", "vietnamese",
                      "semantic_review_status", "approved_target_sense", "candidate_query",
                      "candidate_available"):
            if review.get(field) != baseline.get(field):
                raise ValueError(f"human review changed frozen query context: {review_id} {field}")
        if baseline["candidate_available"] == "True":
            if (any(review.get(field, "").lower() not in {"true", "false"} for field in REVIEW_COLUMNS)
                    or not review.get("reviewer_rationale", "").strip()
                    or not review.get("reviewer_id", "").strip()
                    or not review.get("reviewed_at", "").strip()):
                raise ValueError(f"human review incomplete: {review_id}")
            try:
                datetime.fromisoformat(review["reviewed_at"].replace("Z", "+00:00"))
            except ValueError as error:
                raise ValueError(f"invalid human review timestamp: {review_id}") from error
        by_id[review_id] = review
    labels = {}
    for entry in mapping["mapping"]:
        review = by_id[entry["review_id"]]
        key = (entry["vocab_id"], entry["variant"])
        if key in labels or int(review["source_row_index"]) != entry["source_row_index"]:
            raise ValueError("duplicate or inconsistent blind mapping")
        labels[key] = {"approved": (review["candidate_available"] == "True"
                    and review["correct_intended_meaning"].lower() == "true"
                    and review["visibly_depictable"].lower() == "true"
                    and review["ambiguous_or_wrong_sense"].lower() == "false"
                    and review["inappropriate_text_or_brand_lure"].lower() == "false"),
                       "candidate_query": review["candidate_query"],
                       "review_id": entry["review_id"], "reviewer_id": review["reviewer_id"],
                       "reviewed_at": review["reviewed_at"], "rationale": review["reviewer_rationale"]}
    if records is not None:
        for item in records:
            for variant in VARIANTS:
                if (item["vocab_id"], variant) not in labels:
                    raise ValueError("human review lacks a query variant")
                query = query_contract(item, variant)
                expected = (query["effective_search_query"] if variant == "historical_current"
                            else query["parsed_query"]) or ""
                review_id = labels[item["vocab_id"], variant]["review_id"]
                if by_id[review_id]["candidate_query"] != expected:
                    raise ValueError(f"review query differs from experiment: {review_id}")
    return labels


def review_gate(row: dict, variant: str, label: dict | None) -> str | None:
    if row["semantic_review_status"] == "needs_decision":
        return "pending_semantic_decision"
    if row["semantic_review_status"] == "approved" and not row.get("image_search_intent"):
        return "approved_intent_missing"
    query = query_contract(row, variant)
    if query["skip_reason"]:
        return query["skip_reason"]
    if label is None:
        return "missing_review_labels"
    if "candidate_query" in label and label["candidate_query"] != query["effective_search_query"]:
        return "reviewed_query_differs_from_effective_query"
    if not label.get("approved"):
        return "query_rejected_by_human_review"
    return None


def safe_public_url(value: str, resolver=None) -> str:
    """Reuse collector URL normalization; reject DNS hosts resolving off public internet."""
    try:
        url = normalize_remote_url(value)
        parsed = urlsplit(url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        addresses = (resolver or socket.getaddrinfo)(host, port)
        if not addresses or any(not ipaddress.ip_address(info[4][0]).is_global for info in addresses):
            raise ValueError("private or unresolved address")
    except (CollectionError, OSError, TypeError, ValueError) as error:
        raise ValueError(f"unsafe URL: {error}") from error
    return url


class RateLimiter:
    def __init__(self, interval: float):
        self.interval = interval
        self.next_at = 0.0

    def wait(self) -> None:
        delay = self.next_at - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        self.next_at = time.monotonic() + self.interval


class BingDDGS:
    def __init__(self, timeout: float, retries: int, backoff: float, limiter: RateLimiter):
        self.timeout, self.retries, self.backoff, self.limiter = timeout, retries, backoff, limiter

    def __call__(self, query: str, limit: int) -> tuple[list, float, int]:
        if not 1 <= limit <= 10:
            raise ValueError("result limit must be 1..10")
        from ddgs import DDGS  # Lazy: dry runs and tests cannot import or call DDGS.
        started = time.perf_counter()
        for attempt in range(self.retries + 1):
            self.limiter.wait()
            try:
                raw = DDGS(timeout=self.timeout).images(
                    query=query, region=DDG_REGION, safesearch=DDG_SAFESEARCH,
                    max_results=limit, backend="bing")
                if not isinstance(raw, list):
                    raise ValueError("DDGS returned a non-list result")
                return raw[:limit], time.perf_counter() - started, attempt + 1
            except Exception:
                if attempt == self.retries:
                    raise
                time.sleep(self.backoff * (attempt + 1))
        raise AssertionError("unreachable")


class _PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, port, address, timeout):
        super().__init__(host, port, timeout=timeout, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        sock = socket.create_connection((self.address, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


class _PinnedHTTP(http.client.HTTPConnection):
    def __init__(self, host, port, address, timeout):
        super().__init__(host, port, timeout=timeout)
        self.address = address

    def connect(self):
        self.sock = socket.create_connection((self.address, self.port), self.timeout)


class SafeFetcher:
    """Pin a public resolved IP; never follow redirects or read beyond the size cap."""
    def __init__(self, timeout: float, retries: int, backoff: float, limiter: RateLimiter):
        self.timeout, self.retries, self.backoff, self.limiter = timeout, retries, backoff, limiter

    def __call__(self, url: str) -> tuple[bytes, dict, int, float, int]:
        started = time.perf_counter()
        for attempt in range(self.retries + 1):
            self.limiter.wait()
            connection = None
            try:
                normalized = safe_public_url(url)
                parsed = urlsplit(normalized)
                port = parsed.port or (443 if parsed.scheme == "https" else 80)
                addresses = socket.getaddrinfo(parsed.hostname, port)
                if any(not ipaddress.ip_address(info[4][0]).is_global for info in addresses):
                    raise ValueError("private DNS resolution")
                address = addresses[0][4][0]
                constructor = _PinnedHTTPS if parsed.scheme == "https" else _PinnedHTTP
                connection = constructor(parsed.hostname, port, address, self.timeout)
                target = parsed.path or "/"
                if parsed.query:
                    target += "?" + parsed.query
                connection.request("GET", target, headers={"Host": parsed.netloc, "User-Agent": USER_AGENT})
                response = connection.getresponse()
                headers = {k.lower(): v for k, v in response.getheaders()}
                status = response.status
                if not 200 <= status < 300:
                    raise HTTPStatusError(status)
                if int(headers.get("content-length", "0")) > MAX_IMAGE_BYTES:
                    raise ValueError("image exceeds byte limit")
                body = response.read(MAX_IMAGE_BYTES + 1)
                if len(body) > MAX_IMAGE_BYTES:
                    raise ValueError("image exceeds byte limit")
                return body, headers, status, time.perf_counter() - started, attempt + 1
            except Exception:
                if attempt == self.retries:
                    raise
                time.sleep(self.backoff * (attempt + 1))
            finally:
                if connection is not None:
                    connection.close()
        raise AssertionError("unreachable")


def _metadata_path(variant: str, vocab_id: str, rank: int) -> Path:
    return Path("candidate_metadata") / variant / vocab_id / f"{rank:02d}.json"


def _verify_metadata(run_dir: Path, metadata: dict) -> None:
    if metadata["status"] != "downloaded":
        return
    for path_field, hash_field in (("candidate_path", "original_sha256"),
                                   ("preview_path", "preview_sha256")):
        relative = Path(metadata[path_field])
        path = (run_dir / relative).resolve()
        if not path.is_relative_to(run_dir.resolve()) or not path.is_file() or sha256(path) != metadata[hash_field]:
            raise ValueError(f"candidate hash mismatch: {relative}")


def _seen_hashes(run_dir: Path) -> tuple[set[str], set[str]]:
    urls, hashes = set(), set()
    retained_paths = set()
    for path in (run_dir / "candidate_metadata").glob("*/*/*.json"):
        metadata = json.loads(path.read_text(encoding="utf-8"))
        _verify_metadata(run_dir, metadata)
        if metadata.get("normalized_image_url"):
            urls.add(metadata["normalized_image_url"])
        if metadata.get("original_sha256") and metadata["status"] == "downloaded":
            hashes.add(metadata["original_sha256"])
            retained_paths.update((metadata["candidate_path"], metadata["preview_path"]))
    for path in (run_dir / "candidates").glob("*/*/*"):
        if path.is_file() and path.relative_to(run_dir).as_posix() not in retained_paths:
            raise CandidateIntegrityError(f"orphan candidate file: {path}")
    return urls, hashes


def process_query(run_dir: Path, row: dict, variant: str, search, fetch,
                  resolver=None, limit: int = 10) -> dict:
    """Checkpoint every result; resume verifies retained bytes before any search."""
    if not 1 <= limit <= 10:
        raise ValueError("result limit must be 1..10")
    query = query_contract(row, variant)
    if query["skip_reason"]:
        raise ValueError(query["skip_reason"])
    vocab_id = row["vocab_id"]
    result_path = run_dir / "retrieval_results" / variant / f"{vocab_id}.json"
    urls, hashes = _seen_hashes(run_dir)
    if result_path.exists():
        document = json.loads(result_path.read_text(encoding="utf-8"))
        if (document.get("schema_version") != SCHEMA_VERSION or document.get("vocab_id") != vocab_id
                or document.get("variant") != variant
                or document.get("effective_search_query") != query["effective_search_query"]):
            raise ValueError("retrieval checkpoint does not match frozen query")
        if document.get("status") in {"complete", "search_failed"}:
            return document
    else:
        started = utc_now()
        try:
            search_started = time.perf_counter()
            raw, seconds, attempts = search(query["effective_search_query"], limit)
            if not isinstance(raw, list) or len(raw) > limit:
                raise ValueError("search returned too many or malformed results")
            search_error = None
        except Exception as error:
            raw, seconds, attempts = [], time.perf_counter() - search_started, None
            search_error = f"{type(error).__name__}: {error}"
        document = {"schema_version": SCHEMA_VERSION, "vocab_id": vocab_id,
                    "source_row_index": row["source_row_index"], "variant": variant,
                    "effective_search_query": query["effective_search_query"],
                    "provider": "duckduckgo", "backend": "bing", "region": DDG_REGION,
                    "safesearch": DDG_SAFESEARCH, "max_results": limit,
                    "started_at_utc": started, "search_seconds": seconds,
                    "search_attempts": attempts, "search_error": search_error,
                    "raw_results": json.loads(json.dumps(raw, ensure_ascii=False, default=str)),
                    "results": [], "status": "search_failed" if search_error else "in_progress"}
        json_save(result_path, document)
        if search_error:
            return document
    if len(document["results"]) > len(document["raw_results"]):
        raise ValueError("retrieval checkpoint has excess results")
    for rank, raw in enumerate(document["raw_results"], start=1):
        relative_meta = _metadata_path(variant, vocab_id, rank)
        meta_path = run_dir / relative_meta
        if rank <= len(document["results"]):
            if document["results"][rank - 1].get("metadata_path") != relative_meta.as_posix() or not meta_path.is_file():
                raise ValueError("retrieval checkpoint metadata missing")
            _verify_metadata(run_dir, json.loads(meta_path.read_text(encoding="utf-8")))
            continue
        if meta_path.exists():
            raise ValueError("orphan candidate metadata; manual inspection required")
        raw_dict = raw if isinstance(raw, dict) else {}
        reported_license = raw_dict.get("license") if isinstance(raw_dict.get("license"), str) else None
        metadata = {"schema_version": SCHEMA_VERSION, "candidate_id": f"{variant}-{vocab_id}-{rank:02d}",
                    "vocab_id": vocab_id, "source_row_index": row["source_row_index"],
                    "english": row["english"], "japanese": row["japanese"],
                    "vietnamese": row["vietnamese"], "target_sense": row["target_sense"],
                    "semantic_review_status": row["semantic_review_status"],
                    "approved_image_search_intent": row.get("image_search_intent"),
                    "usage_note": row.get("usage_note"),
                    "visual_type": query["visual_type"], "raw_decoded_text": query["raw_decoded_text"],
                    "raw_model_query": query["parsed_query"], "parsed_query": query["parsed_query"],
                    "effective_search_query": query["effective_search_query"],
                    "visual_description": query["visual_description"],
                    "negative_constraints": query["negative_constraints"],
                    "query_version": query["query_version"], "query_provenance": query["query_provenance"],
                    "retrieval_provider": "duckduckgo", "retrieval_backend": "bing",
                    "retrieval_rank": rank, "search_seconds": document["search_seconds"],
                    "original_result_metadata": raw,
                    "image_url": raw_dict.get("image"), "normalized_image_url": None,
                    "source_page_url": raw_dict.get("url"),
                    "reported_license": reported_license,
                    "license_provenance": "ddgs_result_field" if reported_license else None,
                    "license_unknown": True,
                    "http_status": None, "download_attempts": None, "download_seconds": None,
                    "failure_detail": None, "original_sha256": None, "preview_sha256": None,
                    "candidate_path": None, "preview_path": None, "status": None,
                    "ranking": {"siglip2_model_id": None, "siglip2_revision": None,
                                "scoring_text_variant": None, "raw_score": None,
                                "retrieval_rank": rank, "reranked_position": None,
                                "verifier_result": None, "owner_relevance_label": None}}
        started = time.perf_counter()
        try:
            url = safe_public_url(raw_dict.get("image"), resolver)
            metadata["normalized_image_url"] = url
            if url in urls:
                metadata["status"] = "duplicate_url"
            else:
                urls.add(url)
                try:
                    page = raw_dict.get("url")
                    if page is not None:
                        metadata["source_page_url"] = safe_public_url(page, resolver)
                except ValueError:
                    metadata["source_page_url"] = None
                try:
                    body, headers, http_status, elapsed, attempts = fetch(url)
                    metadata.update(http_status=http_status, download_seconds=elapsed,
                                    download_attempts=attempts, response_headers=headers)
                    if len(body) > MAX_IMAGE_BYTES:
                        raise ValueError("image exceeds byte limit")
                    metadata["original_sha256"] = digest(body)
                    validate_image_bytes(body)
                    if metadata["original_sha256"] in hashes:
                        metadata["status"] = "duplicate_content"
                    else:
                        image_rel = Path("candidates") / variant / vocab_id / f"{rank:02d}.bin"
                        preview_rel = image_rel.with_suffix(".jpg")
                        image_path, preview_path = run_dir / image_rel, run_dir / preview_rel
                        image_path.parent.mkdir(parents=True, exist_ok=True)
                        if image_path.exists() or preview_path.exists():
                            raise CandidateIntegrityError("orphan candidate file; manual inspection required")
                        temporary = image_path.with_name(f".{image_path.name}.{uuid4().hex}.tmp")
                        try:
                            temporary.write_bytes(body)
                            normalize_image_to_jpeg(temporary, preview_path)
                            temporary.rename(image_path)
                        finally:
                            temporary.unlink(missing_ok=True)
                        metadata.update(status="downloaded", candidate_path=image_rel.as_posix(),
                                        preview_path=preview_rel.as_posix(), preview_sha256=sha256(preview_path))
                        hashes.add(metadata["original_sha256"])
                except CandidateIntegrityError:
                    raise
                except Exception as error:
                    if metadata["status"] is None:
                        metadata["status"] = "invalid_image" if metadata["original_sha256"] else "download_failed"
                    metadata["failure_detail"] = f"{type(error).__name__}: {error}"
                    if isinstance(error, HTTPStatusError):
                        metadata["http_status"] = error.status
                    if metadata["download_seconds"] is None:
                        metadata["download_seconds"] = time.perf_counter() - started
        except CandidateIntegrityError:
            raise
        except ValueError as error:
            metadata["status"] = "rejected_url"
            metadata["failure_detail"] = str(error)
        metadata["processing_seconds"] = round(time.perf_counter() - started, 6)
        json_save(meta_path, metadata)
        document["results"].append({"rank": rank, "status": metadata["status"],
                                    "metadata_path": relative_meta.as_posix()})
        json_save(result_path, document)
    document["status"] = "complete"
    document["completed_at_utc"] = utc_now()
    json_save(result_path, document)
    return document


def _tree_hashes(root: Path, directory: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): sha256(path)
            for path in sorted(directory.rglob("*")) if path.is_file()}


def _create_run(root: Path, source: Path, run_dir: Path, source_manifest: dict,
                mode: str, labels_path: Path | None, settings: dict, resume: bool) -> dict:
    if run_dir.exists() and not resume:
        raise ValueError("run directory exists; use --resume or a new run ID")
    if not run_dir.exists() and resume:
        raise ValueError("cannot resume a missing run")
    source_hashes = _tree_hashes(root, source)
    manifest_path = run_dir / "manifests/run_manifest.json"
    if resume:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (manifest["schema_version"] != SCHEMA_VERSION or manifest["mode"] != mode
                or manifest.get("settings") != settings):
            raise ValueError("resume mode/schema mismatch")
        verify_frozen(root, manifest["source_benchmark_hashes"])
        verify_frozen(root, manifest["protected_hashes_before"])
        if manifest["source_benchmark_hashes"] != source_hashes:
            raise ValueError("source benchmark changed")
        for name, expected in manifest["input_snapshot_hashes"].items():
            if sha256(run_dir / "input_snapshot" / name) != expected:
                raise ValueError(f"input snapshot hash mismatch: {name}")
        if labels_path and manifest.get("human_review_sha256") != sha256(labels_path):
            raise ValueError("human review changed since run creation")
        if labels_path and sha256(run_dir / "evaluation/query_labels_reviewed.csv") != manifest["human_review_sha256"]:
            raise ValueError("reviewed-label snapshot changed")
        return manifest
    for name in LAYOUT:
        (run_dir / name).mkdir(parents=True, exist_ok=False)
    snapshots = {}
    for name in ("query_experiment.json", "experiment_manifest.json", "owner_review.csv",
                 "blind_mapping.json", "prompts.json"):
        shutil.copyfile(source / name, run_dir / "input_snapshot" / name)
        snapshots[name] = sha256(run_dir / "input_snapshot" / name)
    for name in ("id_registry_v1.json", "semantic_decisions_v1.json"):
        shutil.copyfile(root / "data/vocabulary" / name, run_dir / "input_snapshot" / name)
        snapshots[name] = sha256(run_dir / "input_snapshot" / name)
    if labels_path:
        shutil.copyfile(labels_path, run_dir / "evaluation/query_labels_reviewed.csv")
    manifest = {"schema_version": SCHEMA_VERSION, "purpose": "isolated_retrieval_candidate_retention",
                "run_id": run_dir.name, "mode": mode, "created_at_utc": utc_now(),
                "source_run_id": source_manifest["run_id"], "source_benchmark_hashes": source_hashes,
                "source_input_hashes": source_manifest["input_hashes"],
                "protected_hashes_before": source_manifest["protected_hashes"],
                "input_snapshot_hashes": snapshots,
                "human_review_sha256": sha256(labels_path) if labels_path else None,
                "provider": "duckduckgo", "backend": "bing", "max_results_per_query": settings["max_results"],
                "settings": settings,
                "status": "in_progress"}
    json_save(manifest_path, manifest)
    return manifest


def run(root: Path, run_id: str, *, live: bool, resume: bool = False,
        labels_path: Path | None = None, source: Path | None = None,
        timeout: float = 12, retries: int = 1, backoff: float = 1,
        rate_interval: float = 2, limit: int = 10, search=None, fetch=None) -> Path:
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("unsafe run ID")
    if not (1 <= limit <= 10 and 1 <= timeout <= 30 and 0 <= retries <= 2
            and 0 <= backoff <= 5 and 0 <= rate_interval <= 30):
        raise ValueError("retrieval settings exceed safe bounds")
    source = source or root / SOURCE_RUN
    records, source_manifest = load_phase_ab(root, source)
    labels = None
    if live:
        if labels_path is None:
            raise ValueError("--live requires a completed, independently reviewed --review-labels file")
        labels = load_review_labels(labels_path, source, records)
    run_dir = root / OUTPUT_BASE / run_id
    settings = {"timeout_seconds": timeout, "retries": retries,
                "backoff_seconds": backoff, "rate_interval_seconds": rate_interval,
                "max_results": limit}
    manifest = _create_run(root, source, run_dir, source_manifest,
                           "live" if live else "dry_run", labels_path, settings, resume)
    manifest_path = run_dir / "manifests/run_manifest.json"
    if live:
        limiter = RateLimiter(rate_interval)
        search = search or BingDDGS(timeout, retries, backoff, limiter)
        fetch = fetch or SafeFetcher(timeout, retries, backoff, limiter)
    gate_rows = []
    retrieval_statuses = {}
    for item in records:
        variant = RETRIEVAL_VARIANT
        label = labels.get((item["vocab_id"], variant)) if labels else None
        reason = review_gate(item, variant, label)
        gate_rows.append({"vocab_id": item["vocab_id"], "source_row_index": item["source_row_index"],
                          "variant": variant, "effective_search_query": query_contract(item, variant)["effective_search_query"] or "",
                          "gate_status": "eligible" if reason is None else "skipped",
                          "skip_reason": reason or "", "review_id": label.get("review_id", "") if label else ""})
        if live and reason is None:
            result = process_query(run_dir, item, variant, search, fetch, limit=limit)
            retrieval_statuses[item["vocab_id"]] = result["status"]
    gate_path = run_dir / "evaluation/query_gate.csv"
    with gate_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(gate_rows[0]))
        writer.writeheader()
        writer.writerows(gate_rows)
    manifest["gate_summary"] = {reason: sum(r["skip_reason"] == reason for r in gate_rows)
                                for reason in sorted({r["skip_reason"] for r in gate_rows})}
    manifest["retrieval_statuses"] = retrieval_statuses
    candidate_statuses = [json.loads(path.read_text(encoding="utf-8"))["status"]
                          for path in (run_dir / "candidate_metadata").glob("*/*/*.json")]
    manifest["candidate_status_counts"] = {status: candidate_statuses.count(status)
                                           for status in sorted(set(candidate_statuses))}
    manifest["status"] = "complete"
    manifest["completed_at_utc"] = utc_now()
    verify_frozen(root, manifest["source_benchmark_hashes"])
    verify_frozen(root, manifest["protected_hashes_before"])
    manifest["hash_verification"] = {"source_benchmark_files": len(manifest["source_benchmark_hashes"]),
                                     "protected_files": len(manifest["protected_hashes_before"]),
                                     "status": "identical", "verified_at_utc": utc_now()}
    json_save(manifest_path, manifest)
    return run_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--dry-run", action="store_true", help="offline gate and layout only")
    choice.add_argument("--live", action="store_true", help="allow DDGS search and image downloads")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--review-labels", type=Path)
    parser.add_argument("--timeout", type=float, default=12)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--backoff", type=float, default=1)
    parser.add_argument("--rate-interval", type=float, default=2)
    parser.add_argument("--max-results", type=int, default=10)
    args = parser.parse_args()
    output = run(PROJECT_ROOT, args.run_id, live=args.live, resume=args.resume,
                 labels_path=args.review_labels, timeout=args.timeout, retries=args.retries,
                 backoff=args.backoff, rate_interval=args.rate_interval, limit=args.max_results)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
