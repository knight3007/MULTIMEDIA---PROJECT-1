"""Verify and report the authorized partial A-004 run without inventing results."""
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "collect data script"))
from imagecollector import is_valid_jpeg

PRELIMINARY = {
    "vocab-000001": ("PASS", "PASS", "UNCHANGED", "Clear apples; A-001 apple also clear."),
    "vocab-000002": ("PASS", "PASS", "UNCHANGED", "Clear bananas; A-001 bananas also clear."),
    "vocab-000003": ("PASS", "NEEDS_REVIEW", "DEGRADED", "Strawberries visible, but unripe fruit and busy foliage reduce clarity versus A-001 isolated berry; a clearer lower-ranked candidate exists."),
    "vocab-000004": ("PASS", "PASS", "UNCHANGED", "Cooked rice in pot matches approved sense; A-001 cooked rice also clear."),
    "vocab-000005": ("PASS", "PASS", "IMPROVED", "Bread is clearer and less crowded than the A-001 bread display."),
    "vocab-000006": ("PASS", "PASS", "UNCHANGED", "Eggs and egg dishes visible; composition appears the same as A-001 at inspection scale."),
    "vocab-000007": ("NEEDS_REVIEW", "FAIL", "UNCHANGED", "MILK DRINKS headline, flavored drinks and collage obscure plain/cow milk; A-001 was also text-heavy. No clearly clean plain-milk candidate in this saved pool."),
    "vocab-000009": ("PASS", "FAIL", "DEGRADED", "Raw chicken meat matches approved sense but has a Depositphotos watermark; a cleaner cooked-chicken candidate ranks lower."),
    "vocab-000010": ("PASS", "FAIL", "DEGRADED", "Breakfast foods appear as separate panels; a clearer single-meal candidate ranks lower than this collage."),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    manifest = json.loads((HERE / "experiment_manifest.json").read_text(encoding="utf-8"))
    queries = json.loads((HERE / "query_results.json").read_text(encoding="utf-8"))
    retrieval = json.loads((HERE / "retrieval_results.json").read_text(encoding="utf-8"))
    with (HERE / "frozen_vocabulary.csv").open(encoding="utf-8-sig", newline="") as stream:
        frozen = list(csv.DictReader(stream))
    with (ROOT / "reports/phase0_quality_review/a001_20261122/preliminary_unverified_baseline_v1.csv").open(encoding="utf-8-sig", newline="") as stream:
        previous = {r["vocab_id"]: r for r in csv.DictReader(stream)}
    ids = [r["vocab_id"] for r in frozen]
    assert len(ids) == len(set(ids)) == len(previous) == len(queries) == 100
    assert set(retrieval).issubset(ids)
    assert sha(ROOT / manifest["dataset_path"]) == manifest["dataset_sha256"]
    assert sha(ROOT / manifest["frozen_vocabulary_path"]) == manifest["frozen_vocabulary_sha256"]
    rankings = []
    for vid, result in retrieval.items():
        for c in result["candidates"]:
            if c["download_status"] == "SUCCESS":
                raw, jpeg = ROOT / c["raw_path"], ROOT / c["jpeg_path"]
                assert raw.is_file() and jpeg.is_file()
                assert sha(raw) == c["raw_sha256"] and sha(jpeg) == c["jpeg_sha256"]
                assert is_valid_jpeg(jpeg)
                with Image.open(raw) as picture:
                    picture.verify()
            rankings.append({"vocab_id": vid, "candidate_id": c["candidate_id"],
                             "retrieval_rank": c["retrieval_rank"], "siglip_rank": c.get("siglip_rank"),
                             "siglip_score": c["siglip_score"], "download_status": c["download_status"],
                             "image_url": c["source"].get("image_url"), "source_page_url": c["source"].get("source_page_url"),
                             "raw_path": c["raw_path"], "raw_sha256": c["raw_sha256"],
                             "jpeg_path": c["jpeg_path"], "jpeg_sha256": c["jpeg_sha256"], "error": c["error"]})
    write_csv(HERE / "candidate_rankings.csv", rankings, list(rankings[0]))
    matrix = []
    for r in frozen:
        vid = r["vocab_id"]
        q = queries[vid]
        result = retrieval.get(vid)
        selected = next((c for c in result["candidates"] if c["candidate_id"] == result["proposed_candidate_id"]), None) if result else None
        relevance, suitability, comparison, note = PRELIMINARY.get(vid, ("NOT_ASSESSED", "NOT_ASSESSED", "NOT_COMPARABLE", ""))
        if not selected:
            relevance, suitability, comparison, note = "NOT_ASSESSED", "NOT_ASSESSED", "NOT_COMPARABLE", "No new ranked image."
        matrix.append({"vocab_id": vid, "english": r["english"], "japanese": r["japanese"],
                       "vietnamese": r["vietnamese"], "expected_semantic_meaning": r["expected_semantic_meaning"],
                       "qwen_status": q["status"], "raw_qwen_output": q["raw_decoded_text"],
                       "normalized_query": q["normalized_query"], "effective_query": q["effective_query"],
                       "query_provenance": q["query_provenance"],
                       "image_status": result["status"] if result else "NOT_RUN_APPROVAL_CREDITS",
                       "search_status": result["search_status"] if result else "NOT_RUN",
                       "downloaded_candidates": sum(c["download_status"] == "SUCCESS" for c in result["candidates"]) if result else 0,
                       "ranking_status": result["ranking_status"] if result else "NOT_RUN",
                       "proposed_candidate_id": result["proposed_candidate_id"] if result else None,
                       "proposed_jpeg_path": selected["jpeg_path"] if selected else None,
                       "proposed_jpeg_sha256": selected["jpeg_sha256"] if selected else None,
                       "previous_a001_image_path": r["previous_image_path"],
                       "previous_a001_image_sha256": r["previous_image_sha256"],
                       "previous_a001_ai_learning_suitability": previous[vid]["ai_image_learning_suitability"],
                       "ai_preliminary_image_relevance": relevance,
                       "ai_preliminary_educational_suitability": suitability,
                       "ai_preliminary_comparison_to_a001": comparison,
                       "ai_preliminary_note": note, "human_review_status": "NOT_REVIEWED"})
    write_csv(HERE / "evaluation_matrix.csv", matrix, list(matrix[0]))
    audio = Counter()
    for old in previous.values():
        path, expected = old["audio_path"], old["audio_sha256"]
        if not path or not expected:
            audio["missing_reference"] += 1
        elif not (ROOT / path).is_file():
            audio["missing_file"] += 1
        elif sha(ROOT / path) != expected:
            audio["hash_mismatch"] += 1
        else:
            audio["hash_match"] += 1
    qcounts = Counter(r["status"] for r in queries.values())
    icounts = Counter(r["status"] for r in retrieval.values())
    downloaded = sum(c["download_status"] == "SUCCESS" for r in retrieval.values() for c in r["candidates"])
    failed_downloads = sum(c["download_status"] == "FAILED" for r in retrieval.values() for c in r["candidates"])
    search_success = sum(r["search_status"] == "SUCCESS" for r in retrieval.values())
    prelim_relevance = Counter(r["ai_preliminary_image_relevance"] for r in matrix)
    prelim_suitability = Counter(r["ai_preliminary_educational_suitability"] for r in matrix)
    comparisons = Counter(r["ai_preliminary_comparison_to_a001"] for r in matrix)
    missing = [vid for vid in ids if vid not in retrieval]
    manifest["status"] = "PARTIAL_STOPPED_AFTER_APPROVAL_CREDIT_BLOCK"
    manifest["completed_query_ids"] = list(queries)
    manifest["completed_image_ids"] = list(retrieval)
    manifest["blockers"] = [{"stage": "image_execution", "reason": "Automatic approval review rejected continuation because workspace is out of credits; 90 remaining image IDs were not executed.",
                             "unprocessed_image_ids": missing}]
    temp = HERE / "experiment_manifest.json.tmp"
    temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(HERE / "experiment_manifest.json")
    report = f"""# A-004 partial run report — 2026-11-23

**Status: PARTIAL, stopped by owner after automatic approval review reported that the workspace was out of credits.** The continuation command for the remaining 90 image IDs was rejected before execution. This is **not** a completed 100-word image rerun. No gallery or human review export was produced for this partial run.

## Frozen execution and actual counts

- Frozen vocabulary: **100/100 unique IDs**, dataset SHA-256 `{manifest['dataset_sha256']}`; exact configuration, Git state, model revisions and code hashes are in `experiment_manifest.json`.
- Qwen local 1.7B: **100/100 IDs attempted exactly once**, raw output retained; **94/100 syntactically valid normalized queries**, of which **93/100 effective queries** can proceed. Six outputs (`go/read/eat/help/choose/swim verb`) failed the existing query validator; ID038 has a valid Qwen query but lacks owner-approved image search intent. No correction retry or old cache was used.
- Image search: **{len(retrieval)}/100 IDs attempted**, **{search_success}/{len(retrieval)} searches succeeded**. The remaining **{len(missing)}/100 IDs were not attempted** due to the approval-credit block. Search settings: one query/ID, up to seven results, 20 s timeout, zero retries. Query status for the unrun image IDs remains in `query_results.json`.
- Candidate downloads: **{downloaded} successful**, **{failed_downloads} failed** among **{len(rankings)} candidate records** from the ten attempted IDs. Each successful raw/JPEG file exists and matches its recorded SHA-256.
- SigLIP: **{icounts['RANKED']}/10 attempted IDs ranked once**; **{icounts['NO_VALID_CANDIDATES']}/10** had no valid download. Proposed top-ranked JPEGs: **{icounts['RANKED']}/100 benchmark IDs**; these are unapproved suggestions. ID008 water returned one URL, which failed with HTTP 404.
- Audio: existing A-001 references **{audio['hash_match']}/100 hash-match**, missing reference {audio['missing_reference']}, missing file {audio['missing_file']}, mismatch {audio['hash_mismatch']}. No audio was regenerated.

## Image quality (AI_PRELIMINARY, 9 visually inspected new top-1 images)

- Semantic relevance: **{prelim_relevance['PASS']}/9 PASS**, **{prelim_relevance['NEEDS_REVIEW']}/9 NEEDS_REVIEW**; 91 benchmark IDs lack a new image judgment. Educational suitability: **{prelim_suitability['PASS']}/9 PASS**, **{prelim_suitability['NEEDS_REVIEW']}/9 NEEDS_REVIEW**, **{prelim_suitability['FAIL']}/9 FAIL**. These are analyst observations, not human verification or public-rights approval.
- A-001 comparison on these same **9/100** IDs: **{comparisons['IMPROVED']} improved, {comparisons['UNCHANGED']} unchanged, {comparisons['DEGRADED']} degraded** (AI_PRELIMINARY). New images are different hashes from A-001; visual descriptions, not a human-verified improvement rate, support these labels. ID008 and 90 unrun IDs are **not comparable**.
- Main observed problems: ID007 milk top-1 is a text-heavy collage and no clearly clean plain-milk candidate appears in its saved pool (retrieval/presentation concern); ID009 chicken meat top-1 has a Depositphotos watermark while a cleaner lower-ranked cooked-chicken candidate exists (ranking/presentation concern); ID010 breakfast top-1 is a multi-panel collage while a clearer lower-ranked meal exists (ranking/presentation concern); ID003 strawberry top-1 includes unripe fruit/clutter while a clearer isolated fruit ranks lower (presentation/ranking concern). ID008 is a candidate URL/download failure, not a proven semantic retrieval failure. No SigLIP blame is assigned without the saved pool.
- `NO_SUITABLE_IMAGE` is an available review outcome; no new owner rejection was inferred. Prior A-003.3 selections and `because` internal-only override were neither copied into this run nor promoted.

## Evidence and limits

`query_results.json` retains raw Qwen output; `retrieval_results.json` retains URL/source, per-candidate errors and score/rank; `candidate_rankings.csv` and `evaluation_matrix.csv` summarize all attempted candidates and all 100 IDs. [Top-1 contact sheet](top1_contact_sheet.jpg), [A-001 comparison sheet](a001_first_batch_contact_sheet.jpg) and [selected pools](candidate_diagnosis_sheet.jpg) support preliminary inspection. The first ten IDs are an ordered slice, not a random sample; no 100-word quality rate can be extrapolated. Full owner review gallery/export was not built because the owner asked to complete only the report of work already run. Game UX/UI remains undecided.

The 90 image IDs remain unexecuted. The exact blocker was automatic approval review failure: **workspace out of credits**. The system stated this was a review failure, not a safety determination, and instructed not to bypass the approval check. Resume only after credits/approval are restored and the owner explicitly asks to continue; the frozen run ledgers prevent rerunning completed IDs. B-003.2 remains paused.
"""
    (HERE / "evaluation_report.md").write_text(report, encoding="utf-8")
    print("query", dict(qcounts), "image", dict(icounts), "downloaded", downloaded, "audio", dict(audio))


if __name__ == "__main__":
    main()
