"""Validate the owner's A004R follow-up export and write the final 100-ID image selection manifest.

Read-only on every earlier experiment. Outputs (this folder): owner_followup_export.json (copy),
final_selection_manifest.json, final_selection.csv, strategy_summary.json. No network or model use.
"""
import csv
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
EXP = ROOT / "reports/image_pipeline_experiments"
FU = EXP / "A004R_OWNER_FOLLOWUP_100"
SOURCE_EXPORT = Path("D:/Download/A004R-followup-review-2026-11-23.json")
COPY = HERE / "owner_followup_export.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def check(path, digest):
    target = (ROOT / path).resolve()
    if Path(path).is_absolute() or not target.is_relative_to(ROOT.resolve()) or not target.is_file() or sha(target) != digest:
        raise ValueError(f"path/hash mismatch: {path}")


def origin(vid, path, cid, plan_item, ctx):
    """Map a selected file to the experiment, query strategy and exact query that produced it."""
    if path.startswith("reports/image_pipeline_experiments/A004_FULL_100_RERUN/"):
        return "A-004", "QWEN_DEFAULT", ctx["a004"][vid]["query"]
    if path.startswith("reports/image_pipeline_experiments/A004R_CONDITIONAL_100/"):
        route = ctx["routes"][vid]
        return "A-004R", "ICON_WORD" if route["routing_strategy"] == "ICON" else "QWEN_DEFAULT", route["experimental_search_query"]
    if path.startswith("reports/image_pipeline_experiments/A003_CONDITIONAL_SEARCH/"):
        sample = ctx["a003"][vid]
        return ("A-003", "ICON_WORD", sample["icon_query"]) if "/ICON/" in path else ("A-003", "QWEN_DEFAULT", sample["normal_query"])
    if path.startswith("reports/image_pipeline_experiments/A004R_OWNER_FOLLOWUP_100/"):
        result = ctx["followup"][vid]
        attempts = [result] + result.get("previous_attempts", [])
        attempt = next(a for a in attempts if any(c["candidate_id"] == cid for c in a["candidates"]))
        query = attempt["query"]
        return "A-004R-FU", "ICON_DESCRIPTIVE" if query.endswith(" icon") else "SCENE_DESCRIPTIVE", query
    if path.startswith("reports/image_pipeline_experiments/A002_CAUSAL_CONCEPT_PILOT/"):
        return "A-002-CAUSAL", "CURATED_CONCEPT", "cause effect visual sequence illustration"
    if path.startswith(("baseline/media-staging/", "data/image/en/")):
        return "A-001", "QWEN_DEFAULT_A001", ctx["a001"][vid]["effective_image_query"]
    raise ValueError(f"unknown origin: {vid} {path}")


def main():
    if not COPY.exists():
        shutil.copyfile(SOURCE_EXPORT, COPY)
    if sha(COPY) != sha(SOURCE_EXPORT):
        raise ValueError("export copy differs from the Download file")
    export, plan = read(COPY), read(FU / "followup_plan.json")
    if export["task_id"] != plan["task_id"] or export["source_export_sha256"] != plan["source_export_sha256"]:
        raise ValueError("export does not belong to the frozen follow-up plan")
    items = {i["vocab_id"]: i for i in plan["items"]}
    reviews = export["reviews"]
    if len(reviews) != 100 or {r["vocab_id"] for r in reviews} != set(items):
        raise ValueError("export must cover exactly the 100 plan IDs")
    ctx = {"a004": read(EXP / "A004_FULL_100_RERUN/retrieval_results.json"),
           "routes": {r["vocab_id"]: r for r in rows(EXP / "A004R_CONDITIONAL_100/routing_matrix.csv")},
           "a003": {r["vocab_id"]: r for r in rows(EXP / "A003_CONDITIONAL_SEARCH/frozen_sample.csv")},
           "followup": read(FU / "retrieval_results.json"),
           "a001": {x["vocab_id"]: x for x in read(ROOT / "reports/phase0_quality_review/a001_20261122/evaluation_matrix.json")["items"]}}
    final = []
    for review in sorted(reviews, key=lambda r: r["vocab_id"]):
        vid, item = review["vocab_id"], items[review["vocab_id"]]
        if review["carried_forward"]:
            fixed = item["fixed"]
            if not fixed or (review["candidate_id"], review["path"], review["sha256"]) != (fixed["candidate_id"], fixed["path"], fixed["sha256"]):
                raise ValueError(f"carried-forward row differs from frozen plan: {vid}")
            cid, path, digest, label, decision = fixed["candidate_id"], fixed["path"], fixed["sha256"], "PASS", fixed["source"]
        else:
            if item["fixed"]:
                raise ValueError(f"fixed ID exported as open: {vid}")
            cid, label = review["selected_candidate_id"], review["image_label"]
            path, digest = review["selected_jpeg_path"], review["selected_jpeg_sha256"]
            if cid == "NO_SUITABLE_IMAGE" or label != "PASS" or not path:
                raise ValueError(f"open item without a PASS image: {vid} {cid} {label}")
            decision = "A004R_FU_OWNER_PASS"
        check(path, digest)
        experiment, strategy, query = origin(vid, path, cid, item, ctx)
        restriction = "INTERNAL_ONLY_TEMPORARY" if decision == "INTERNAL_ONLY_TEMPORARY" else "NOT_PROMOTED"
        final.append({"vocab_id": vid, "english": item["english"], "japanese": item["japanese"], "vietnamese": item["vietnamese"],
                      "selected_candidate_id": cid, "image_path": path, "image_sha256": digest, "owner_label": label,
                      "owner_decision_source": decision, "source_experiment": experiment, "query_strategy": strategy,
                      "search_query": query, "owner_note": item["owner_note"], "usage_restriction": restriction,
                      "rights": "UNKNOWN_NOT_CLEARED"})
    by_strategy = Counter(r["query_strategy"] for r in final)
    by_experiment = Counter(r["source_experiment"] for r in final)
    manifest = {"task_id": "A004R_FINAL_SELECTION", "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "reviewer": export["reviewer"], "owner_export_sha256": sha(COPY),
                "followup_plan_sha256": sha(FU / "followup_plan.json"),
                "dataset_sha256": plan["dataset_sha256"], "count": len(final),
                "with_image": sum(bool(r["image_path"]) for r in final),
                "by_query_strategy": dict(by_strategy), "by_source_experiment": dict(by_experiment),
                "status": "OWNER_APPROVED_QUALITY_SELECTION_NOT_PROMOTED",
                "note": "Owner image-quality choice only. Rights unknown; vocab-000081 is internal-only. Not written to data/ or unified_dataset_v1.json.",
                "items": final}
    (HERE / "final_selection_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (HERE / "final_selection.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(final[0]))
        writer.writeheader()
        writer.writerows(final)
    print(len(final), "IDs;", dict(by_strategy), dict(by_experiment))


if __name__ == "__main__":
    main()
