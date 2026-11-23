"""Freeze and execute the isolated A-004R conditional-query experiment."""
import argparse
import csv
import hashlib
import json
import os
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
A004 = HERE.parent / "A004_FULL_100_RERUN"
sys.path.insert(0, str(ROOT / "collect data script"))
import imagecollector as image
from image_scorer import SiglipImageScorer, flatten_to_rgb

ROUTES = HERE / "routing_matrix.csv"
MANIFEST = HERE / "experiment_manifest.json"
RESULTS = HERE / "retrieval_results.json"
OWNER = ROOT / "reports/image_pipeline_experiments/A003_OWNER_DECISIONS/final_image_selection_manifest.json"
OVERRIDES = ROOT / "data/vocabulary/internal_image_overrides_v1.json"
PILOT_IDS = [1, 28, 56, 53, 65, 46, 57, 83, 81, 41]
ICON_NEW = {19, 53, 56, 61, 62, 65}
NORMAL_NEW = {1, 8, 28}
SPECIAL_EXTRA = {86, 92, 96}
FIELDS = ["order", "vocab_id", "english", "japanese", "vietnamese", "original_qwen_query",
          "intended_meaning", "routing_strategy", "experimental_search_query", "routing_rationale",
          "supporting_evidence", "owner_candidate_id", "owner_image_path", "owner_image_sha256",
          "owner_decision", "usage_restriction", "public_eligibility", "execution_source",
          "new_retrieval_needed", "query_review_flag", "a001_image_path", "a001_image_sha256",
          "a004_image_path", "a004_image_sha256"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(temp, path)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def verify_inputs():
    a004_manifest = load_json(A004 / "experiment_manifest.json")
    assert sha(ROOT / a004_manifest["dataset_path"]) == a004_manifest["dataset_sha256"]
    assert sha(A004 / "frozen_vocabulary.csv") == a004_manifest["frozen_vocabulary_sha256"]
    frozen = read_csv(A004 / "frozen_vocabulary.csv")
    matrix = {r["vocab_id"]: r for r in read_csv(A004 / "evaluation_matrix.csv")}
    queries = load_json(A004 / "query_results.json")
    old = load_json(A004 / "retrieval_results.json")
    owner = load_json(OWNER)
    override = load_json(OVERRIDES)["overrides"]
    ids = [r["vocab_id"] for r in frozen]
    assert len(ids) == len(set(ids)) == len(matrix) == len(queries) == len(old) == 100
    assert set(ids) == set(matrix) == set(queries) == set(old)
    assert len(owner["approved_image_selections"]) == 6
    assert len(owner["no_suitable_image_outcomes"]) == len(override) == 1
    approved = {r["vocab_id"]: r for r in owner["approved_image_selections"]}
    no_image = {r["vocab_id"]: r for r in owner["no_suitable_image_outcomes"]}
    internal = {r["vocab_id"]: r for r in override}
    assert len(approved) == 6 and set(no_image) == {"vocab-000083"} and set(internal) == {"vocab-000081"}
    for item in [*approved.values(), *internal.values()]:
        path = ROOT / item.get("image_path")
        assert path.is_file() and sha(path) == item["image_sha256"], path
    assert owner["because_restriction_unchanged"]["usage_restriction"] == "INTERNAL_ONLY_TEMPORARY"
    assert internal["vocab-000081"]["public_use"] == "NOT_ALLOWED_UNTIL_RIGHTS_CLEARED_OR_REPLACED"
    assert image.normalize_image_to_jpeg.__globals__["flatten_to_rgb"] is flatten_to_rgb
    assert SiglipImageScorer.score_batch.__globals__["flatten_to_rgb"] is flatten_to_rgb
    return a004_manifest, frozen, matrix, queries, old, approved, no_image, internal


def build_routes(frozen, matrix, queries, old, approved, no_image, internal):
    ids = [r["vocab_id"] for r in frozen]
    if len(ids) != len(set(ids)) or len(ids) != 100 or set(ids) != set(matrix) or set(ids) != set(queries) or set(ids) != set(old):
        raise ValueError("Routing requires exactly 100 unique matching vocabulary IDs")
    by_id = {r["vocab_id"]: r for r in frozen}
    order = [f"vocab-{n:06d}" for n in PILOT_IDS] + [vid for vid in ids if vid not in {f"vocab-{n:06d}" for n in PILOT_IDS}]
    routes = []
    for index, vid in enumerate(order, 1):
        word = by_id[vid]
        q = queries[vid]
        old_row = matrix[vid]
        number = int(vid.rsplit("-", 1)[1])
        owner_item = approved.get(vid)
        internal_item = internal.get(vid)
        query = q.get("effective_query") or ""
        strategy, source, actual, rationale, evidence = "SPECIAL_REVIEW", "BLOCKED_QUERY", "", "", "A-004 query ledger"
        if vid in no_image:
            source, rationale, evidence = "NO_SUITABLE_IMAGE", "Owner accepted no suitable image; do not force a top-1", "A-003.3 owner decision"
        elif internal_item:
            source, rationale, evidence = "INTERNAL_OVERRIDE", "Owner's temporary internal-only because image; no fresh search", "D-015/D-016; A-002 causal pilot"
        elif owner_item:
            strategy = "ICON" if "-ICON-" in owner_item["candidate_id"] else "NORMAL"
            source, rationale, evidence = "OWNER_REFERENCE", "Preserve exact owner-selected quality image, independent of SigLIP", "A-003.3 owner decision"
        elif number in ICON_NEW:
            strategy, source, actual = "ICON", "NEW_RETRIEVAL", word["english"] + " icon"
            rationale, evidence = "Icon arm has per-ID pilot evidence; review text and watermark contamination", "A-002 icon pilot"
        elif number in SPECIAL_EXTRA or q["status"] != "SUCCESS" or old_row["ai_preliminary_query_correctness"] == "FAIL":
            rationale = "QUERY_NEEDS_REPAIR or ambiguous sense; no authorized replacement query"
            evidence = "A-004 query/image review"
        else:
            strategy, actual = "NORMAL", query
            source = "NEW_RETRIEVAL" if number in NORMAL_NEW or old[vid]["status"] != "RANKED" else "A004_REUSE"
            rationale = "Concrete/usable existing query; A-004 result reused when valid" if source == "A004_REUSE" else "Normal-query verification or prior technical failure"
            evidence = "A-004 baseline and A-001 meaning"
        if source in {"NEW_RETRIEVAL", "A004_REUSE"} and not actual:
            raise ValueError(f"Missing executable query: {vid}")
        if source == "A004_REUSE" and old[vid]["query"] != actual:
            raise ValueError(f"Cached query mismatch: {vid}")
        if strategy == "NORMAL" and actual.endswith(" icon"):
            raise ValueError(f"Normal route contains icon query: {vid}")
        if strategy == "ICON" and source == "NEW_RETRIEVAL" and actual != word["english"] + " icon":
            raise ValueError(f"Bad icon query: {vid}")
        selection = owner_item or internal_item or {}
        routes.append({"order": index, "vocab_id": vid, "english": word["english"],
                       "japanese": word["japanese"], "vietnamese": word["vietnamese"],
                       "original_qwen_query": q.get("normalized_query") or q.get("raw_decoded_text") or "",
                       "intended_meaning": word["expected_semantic_meaning"], "routing_strategy": strategy,
                       "experimental_search_query": actual, "routing_rationale": rationale,
                       "supporting_evidence": evidence, "owner_candidate_id": selection.get("candidate_id") or selection.get("selection", {}).get("candidate_id", ""),
                       "owner_image_path": selection.get("image_path", ""), "owner_image_sha256": selection.get("image_sha256", ""),
                       "owner_decision": "OWNER_ACCEPTED" if owner_item else "NO_SUITABLE_IMAGE" if vid in no_image else "INTERNAL_ONLY_TEMPORARY" if internal_item else "NOT_REVIEWED",
                       "usage_restriction": "INTERNAL_ONLY_TEMPORARY" if internal_item else "NOT_PROMOTED",
                       "public_eligibility": selection.get("public_eligibility") or selection.get("public_use") or "UNKNOWN_RIGHTS_NOT_CLEARED",
                       "execution_source": source, "new_retrieval_needed": source == "NEW_RETRIEVAL",
                       "query_review_flag": old_row["ai_preliminary_query_correctness"],
                       "a001_image_path": word["previous_image_path"] if word["previous_image_path"] != "MISSING_EVIDENCE" else "",
                       "a001_image_sha256": word["previous_image_sha256"] if word["previous_image_path"] != "MISSING_EVIDENCE" else "",
                       "a004_image_path": old_row["proposed_jpeg_path"], "a004_image_sha256": old_row["proposed_jpeg_sha256"]})
    return routes


def freeze():
    if ROUTES.exists() or MANIFEST.exists() or RESULTS.exists():
        raise FileExistsError("A-004R is already frozen; refusing to overwrite")
    a004, frozen, matrix, queries, old, approved, no_image, internal = verify_inputs()
    routes = build_routes(frozen, matrix, queries, old, approved, no_image, internal)
    write_csv(ROUTES, routes)
    config = {"task_id": "A-004R", "status": "FROZEN_OFFLINE", "created_at": now(),
              "dataset_path": a004["dataset_path"], "dataset_sha256": a004["dataset_sha256"],
              "source_a004": "reports/image_pipeline_experiments/A004_FULL_100_RERUN",
              "a004_manifest_sha256": sha(A004 / "experiment_manifest.json"),
              "a004_queries_sha256": sha(A004 / "query_results.json"),
              "a004_retrieval_sha256": sha(A004 / "retrieval_results.json"),
              "a004_matrix_sha256": sha(A004 / "evaluation_matrix.csv"),
              "owner_manifest_sha256": sha(OWNER), "override_sha256": sha(OVERRIDES),
              "routing_matrix_sha256": sha(ROUTES), "runner_sha256": sha(__file__),
              "collector_sha256": sha(ROOT / "collect data script/imagecollector.py"),
              "scorer_sha256": sha(ROOT / "collect data script/image_scorer.py"),
              "retrieval": a004["retrieval"], "ranking": a004["ranking"],
              "preprocessing": a004["preprocessing"], "pilot_ids": [f"vocab-{n:06d}" for n in PILOT_IDS],
              "batches": [], "completed_ids": []}
    save_json(MANIFEST, config)
    from collections import Counter
    counts = Counter(r["routing_strategy"] for r in routes)
    sources = Counter(r["execution_source"] for r in routes)
    lines = ["# A-004R frozen routing preview", "", f"100 unique IDs; strategy {dict(counts)}; execution source {dict(sources)}.",
             "", "Initial 10 IDs (frozen order):", ""]
    lines += [f"- {r['vocab_id']} {r['english']}: {r['routing_strategy']} / {r['execution_source']} / `{r['experimental_search_query']}`" for r in routes[:10]]
    lines += ["", "ICON queries to execute:", ""]
    lines += [f"- {r['vocab_id']}: `{r['experimental_search_query']}`" for r in routes if r["routing_strategy"] == "ICON" and r["new_retrieval_needed"]]
    lines += ["", "All other results are explicitly reused from A-004, bound to owner references, or blocked with rationale in the matrix. No owner reference is counted as a new retrieval. No production asset is written.", ""]
    (HERE / "routing_preview.md").write_text("\n".join(lines), encoding="utf-8")
    print(dict(counts), dict(sources), "routing_sha256", config["routing_matrix_sha256"])


def guard(manifest):
    assert sha(ROOT / manifest["dataset_path"]) == manifest["dataset_sha256"]
    for name, path in [("a004_manifest_sha256", A004 / "experiment_manifest.json"),
                       ("a004_queries_sha256", A004 / "query_results.json"),
                       ("a004_retrieval_sha256", A004 / "retrieval_results.json"),
                       ("a004_matrix_sha256", A004 / "evaluation_matrix.csv"),
                       ("owner_manifest_sha256", OWNER), ("override_sha256", OVERRIDES),
                       ("routing_matrix_sha256", ROUTES), ("runner_sha256", Path(__file__)),
                       ("collector_sha256", ROOT / "collect data script/imagecollector.py"),
                       ("scorer_sha256", ROOT / "collect data script/image_scorer.py")]:
        assert sha(path) == manifest[name], f"Frozen source changed: {path}"
    rows = read_csv(ROUTES)
    assert len(rows) == len({r["vocab_id"] for r in rows}) == 100
    return rows


def run(max_batches):
    manifest = load_json(MANIFEST)
    routes = guard(manifest)
    results = load_json(RESULTS) if RESULTS.exists() else {}
    for result in results.values():
        if result["status"] == "ATTEMPTED":
            result.update(status="INTERRUPTED", error="Interrupted after attempt began; not retried automatically",
                          finished_at=now())
    if results:
        save_json(RESULTS, results)
    pending = [r for r in routes if r["vocab_id"] not in results]
    if not pending:
        print("A-004R all 100 IDs already processed")
        return
    old = load_json(A004 / "retrieval_results.json")
    scorer = None
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    for start in range(0, len(pending), 10):
        if max_batches is not None and start // 10 >= max_batches:
            break
        batch = pending[start:start + 10]
        for row in batch:
            vid, source, query = row["vocab_id"], row["execution_source"], row["experimental_search_query"]
            result = {"vocab_id": vid, "routing_strategy": row["routing_strategy"], "query": query,
                      "execution_source": source, "status": "ATTEMPTED", "search_attempted": False,
                      "search_status": "NOT_RUN", "raw_result_count": 0, "candidates": [],
                      "score_attempted": False, "ranking_status": "NOT_RUN", "proposed_candidate_id": None,
                      "owner_candidate_id": row["owner_candidate_id"], "owner_image_path": row["owner_image_path"],
                      "owner_image_sha256": row["owner_image_sha256"], "owner_decision": row["owner_decision"],
                      "usage_restriction": row["usage_restriction"], "public_eligibility": row["public_eligibility"],
                      "human_approval_of_new_image": "NOT_REVIEWED", "error": None, "attempted_at": now()}
            results[vid] = result
            save_json(RESULTS, results)
            if source == "A004_REUSE":
                cached = old[vid]
                result.update(status="REUSED_A004", search_status=cached["search_status"],
                              raw_result_count=cached["raw_result_count"], candidates=deepcopy(cached["candidates"]),
                              ranking_status=cached["ranking_status"], proposed_candidate_id=cached["proposed_candidate_id"],
                              provenance={"experiment": "A004_FULL_100_RERUN", "retrieval_sha256": manifest["a004_retrieval_sha256"],
                                          "source_status": cached["status"], "new_search": False, "new_scoring": False})
            elif source != "NEW_RETRIEVAL":
                result.update(status=source, error=row["routing_rationale"] if source == "BLOCKED_QUERY" else None)
            else:
                try:
                    if scorer is None:
                        scorer = SiglipImageScorer(device="auto", dtype="auto")
                        manifest["ranking"]["a004r_actual_device"] = scorer.device
                        manifest["ranking"]["a004r_actual_dtype"] = str(scorer.dtype)
                        manifest["ranking"]["a004r_model_path"] = scorer.model_path
                        save_json(MANIFEST, manifest)
                    result["search_attempted"] = True
                    save_json(RESULTS, results)
                    found = image.search_images(query, page_size=7, timeout=20, retries=0, retry_delay=2, backend="auto")
                    result.update(search_status="SUCCESS", raw_result_count=found.raw_count,
                                  search_backend=found.backend, search_seconds=found.duration_seconds)
                    for n, candidate in enumerate(found.candidates[:7], 1):
                        result["candidates"].append({"candidate_id": f"{vid}-A004R-{n:02d}", "retrieval_rank": n,
                                                     "source": candidate, "download_status": "NOT_ATTEMPTED",
                                                     "raw_path": None, "raw_sha256": None, "jpeg_path": None,
                                                     "jpeg_sha256": None, "siglip_score": None, "error": None})
                    save_json(RESULTS, results)
                    paths = []
                    for c in result["candidates"]:
                        number = c["retrieval_rank"]
                        folder = HERE / "images" / vid
                        folder.mkdir(parents=True, exist_ok=True)
                        raw, jpeg = folder / f"{number:02d}.img", folder / f"{number:02d}.jpg"
                        c["download_status"] = "ATTEMPTED"
                        save_json(RESULTS, results)
                        try:
                            image.download_candidate_image(c["source"]["image_url"], raw, timeout=20, retries=0, retry_delay=2)
                            image.normalize_image_to_jpeg(raw, jpeg)
                            c.update(download_status="SUCCESS", raw_path=raw.relative_to(ROOT).as_posix(),
                                     raw_sha256=sha(raw), jpeg_path=jpeg.relative_to(ROOT).as_posix(), jpeg_sha256=sha(jpeg))
                            paths.append(raw)
                        except Exception as error:
                            c.update(download_status="FAILED", error=f"{type(error).__name__}: {error}")
                        save_json(RESULTS, results)
                    if not paths:
                        result.update(status="NO_VALID_CANDIDATES", error="No valid candidate downloaded")
                    else:
                        result["score_attempted"] = True
                        save_json(RESULTS, results)
                        scores = scorer.score_batch(query, paths)
                        score_map = {str(s.image_path): s.score for s in scores}
                        for c in result["candidates"]:
                            if c["download_status"] == "SUCCESS":
                                c["siglip_score"] = float(score_map[str(ROOT / c["raw_path"])])
                        ranked = sorted((c for c in result["candidates"] if c["siglip_score"] is not None),
                                        key=lambda c: c["siglip_score"], reverse=True)
                        for position, c in enumerate(ranked, 1):
                            c["siglip_rank"] = position
                        result.update(status="RANKED_NEW", ranking_status="SUCCESS", proposed_candidate_id=ranked[0]["candidate_id"])
                except Exception as error:
                    result.update(status="FAILED", error=f"{type(error).__name__}: {error}")
            result["finished_at"] = now()
            save_json(RESULTS, results)
            manifest["completed_ids"] = list(results)
            manifest["status"] = "IN_PROGRESS"
            save_json(MANIFEST, manifest)
            print(vid, row["routing_strategy"], source, result["status"], flush=True)
        manifest["batches"].append({"ids": [r["vocab_id"] for r in batch], "saved_at": now()})
        save_json(MANIFEST, manifest)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["freeze", "verify", "run"])
    parser.add_argument("--max-batches", type=int)
    args = parser.parse_args()
    if args.phase == "freeze":
        freeze()
    elif args.phase == "verify":
        rows = guard(load_json(MANIFEST))
        print("Frozen routing verified", len(rows), "IDs")
    else:
        if args.max_batches is not None and args.max_batches < 1:
            parser.error("--max-batches must be positive")
        run(args.max_batches)


if __name__ == "__main__":
    main()
