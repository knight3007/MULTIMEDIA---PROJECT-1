"""Verify the resumed A-004 ledger and write its 100-ID evaluation package."""
import csv
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

# Desk review of the frozen English/Vietnamese words against actual effective queries.
# These are AI_PRELIMINARY labels, separate from syntactic validator results.
QUERY_FAIL = {18, 19, 36, 41, 42, 43, 47, 48, 50, 53, 54, 55, 56, 62, 66, 74, 75, 77, 82, 84, 87, 88}
QUERY_REVIEW = {21, 30, 31, 33, 46, 49, 58, 59, 61, 63, 67, 68, 69, 70, 71, 72, 78, 79, 80, 81, 83, 85, 86}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main():
    manifest = json.loads((HERE / "experiment_manifest.json").read_text(encoding="utf-8"))
    queries = json.loads((HERE / "query_results.json").read_text(encoding="utf-8"))
    retrieval = json.loads((HERE / "retrieval_results.json").read_text(encoding="utf-8"))
    with (HERE / "frozen_vocabulary.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    with (ROOT / "reports/phase0_quality_review/a001_20261122/preliminary_unverified_baseline_v1.csv").open(encoding="utf-8-sig", newline="") as stream:
        previous = {r["vocab_id"]: r for r in csv.DictReader(stream)}
    with (HERE / "evaluation_matrix_partial_10.csv").open(encoding="utf-8-sig", newline="") as stream:
        initial = {r["vocab_id"]: r for r in csv.DictReader(stream)}
    assessments_path = HERE / "ai_preliminary_assessments.psv"
    with assessments_path.open(encoding="utf-8", newline="") as stream:
        assessments = {r["vocab_id"]: r for r in csv.DictReader(stream, delimiter="|")}
    ids = [r["vocab_id"] for r in rows]
    assert len(ids) == len(set(ids)) == len(queries) == len(retrieval) == len(previous) == 100
    assert set(ids) == set(queries) == set(retrieval)
    assert sha(ROOT / manifest["dataset_path"]) == manifest["dataset_sha256"]
    assert sha(ROOT / manifest["frozen_vocabulary_path"]) == manifest["frozen_vocabulary_sha256"]
    for name, expected in manifest["source_code_sha256"].items():
        assert sha(ROOT / "collect data script" / name) == expected, name
    assert sha(HERE / "run_a004.py") == manifest["runner_sha256"]
    assert len([b for b in manifest["batches"] if b["phase"] == "image"]) == 10
    batch_ids = [vid for b in manifest["batches"] if b["phase"] == "image" for vid in b["ids"]]
    assert len(batch_ids) == len(set(batch_ids)) == 100 and set(batch_ids) == set(ids)
    candidates = []
    matrix = []
    for row in rows:
        vid = row["vocab_id"]
        q, result = queries[vid], retrieval[vid]
        assert result["vocab_id"] == vid
        if q["status"] != "SUCCESS":
            assert result["status"] == "SKIPPED_QUERY" and not result["search_attempted"]
        elif result["status"] == "RANKED":
            assert result["search_attempted"] and result["ranking_status"] == "SUCCESS"
        valid = []
        for c in result["candidates"]:
            assert c["candidate_id"].startswith(vid + "-")
            if c["download_status"] == "SUCCESS":
                raw, jpeg = ROOT / c["raw_path"], ROOT / c["jpeg_path"]
                assert raw.is_file() and jpeg.is_file()
                assert sha(raw) == c["raw_sha256"] and sha(jpeg) == c["jpeg_sha256"]
                with Image.open(raw) as im:
                    im.verify()
                with Image.open(jpeg) as im:
                    assert im.format == "JPEG"
                    im.verify()
                valid.append(c)
            candidates.append({"vocab_id": vid, "candidate_id": c["candidate_id"],
                               "retrieval_rank": c["retrieval_rank"], "download_status": c["download_status"],
                               "siglip_rank": c.get("siglip_rank"), "siglip_score": c.get("siglip_score"),
                               "image_url": c["source"].get("image_url"),
                               "source_page_url": c["source"].get("source_page_url"),
                               "raw_path": c["raw_path"], "raw_sha256": c["raw_sha256"],
                               "jpeg_path": c["jpeg_path"], "jpeg_sha256": c["jpeg_sha256"], "error": c["error"]})
        if result["status"] == "RANKED":
            assert valid and {c["siglip_rank"] for c in valid} == set(range(1, len(valid) + 1))
            best = max(valid, key=lambda c: c["siglip_score"])
            assert best["candidate_id"] == result["proposed_candidate_id"] and best["siglip_rank"] == 1
        else:
            assert not result["proposed_candidate_id"]
        selected = next((c for c in valid if c["candidate_id"] == result["proposed_candidate_id"]), None)
        prior = initial[vid]
        assessment = assessments.get(vid, {})
        relevance = assessment.get("relevance", prior["ai_preliminary_image_relevance"])
        suitability = assessment.get("suitability", prior["ai_preliminary_educational_suitability"])
        comparison = assessment.get("comparison", prior["ai_preliminary_comparison_to_a001"])
        note = assessment.get("note", prior["ai_preliminary_note"])
        if not selected:
            relevance, suitability, comparison = "NOT_ASSESSED", "NOT_ASSESSED", "NOT_COMPARABLE"
            note = result.get("error") or q.get("error") or "No ranked image"
        number = int(vid.rsplit("-", 1)[1])
        query_label = "BLOCKED" if q["status"] != "SUCCESS" else ("FAIL" if number in QUERY_FAIL else "NEEDS_REVIEW" if number in QUERY_REVIEW else "PASS")
        matrix.append({"vocab_id": vid, "english": row["english"], "japanese": row["japanese"],
                       "vietnamese": row["vietnamese"], "expected_semantic_meaning": row["expected_semantic_meaning"],
                       "qwen_status": q["status"], "raw_qwen_output": q["raw_decoded_text"],
                       "normalized_query": q["normalized_query"], "effective_query": q["effective_query"],
                       "query_provenance": q["query_provenance"],
                       "ai_preliminary_query_correctness": query_label,
                       "image_status": result["status"], "search_status": result["search_status"],
                       "downloaded_candidates": len(valid), "ranking_status": result["ranking_status"],
                       "proposed_candidate_id": result["proposed_candidate_id"],
                       "proposed_jpeg_path": selected["jpeg_path"] if selected else None,
                       "proposed_jpeg_sha256": selected["jpeg_sha256"] if selected else None,
                       "previous_a001_image_path": row["previous_image_path"],
                       "previous_a001_image_sha256": row["previous_image_sha256"],
                       "previous_a001_ai_learning_suitability": previous[vid]["ai_image_learning_suitability"],
                       "ai_preliminary_image_relevance": relevance,
                       "ai_preliminary_educational_suitability": suitability,
                       "ai_preliminary_comparison_to_a001": comparison,
                       "ai_preliminary_note": note, "human_review_status": "NOT_REVIEWED"})
    for row in matrix:
        if row["previous_a001_image_path"] and row["previous_a001_image_path"] != "MISSING_EVIDENCE":
            path = ROOT / row["previous_a001_image_path"]
            assert path.is_file() and sha(path) == row["previous_a001_image_sha256"]
    audio = Counter()
    for old in previous.values():
        path, expected = old["audio_path"], old["audio_sha256"]
        audio["hash_match" if path and expected and (ROOT / path).is_file() and sha(ROOT / path) == expected else "missing_or_mismatch"] += 1
    assert audio["hash_match"] == 100
    write_csv(HERE / "candidate_rankings.csv", candidates)
    write_csv(HERE / "evaluation_matrix.csv", matrix)
    blocked = [{"vocab_id": vid, "english": next(r["english"] for r in rows if r["vocab_id"] == vid),
                "query_status": queries[vid]["status"], "raw_qwen_output": queries[vid]["raw_decoded_text"],
                "reason": queries[vid]["error"]} for vid in ids if queries[vid]["status"] != "SUCCESS"]
    write_json(HERE / "query_remediation.json", blocked)
    qcounts = Counter(q["status"] for q in queries.values())
    icounts = Counter(r["status"] for r in retrieval.values())
    downloads = Counter(c["download_status"] for r in retrieval.values() for c in r["candidates"])
    search_attempts = sum(r["search_attempted"] for r in retrieval.values())
    search_successes = sum(r["search_status"] == "SUCCESS" for r in retrieval.values())
    relevance = Counter(r["ai_preliminary_image_relevance"] for r in matrix)
    suitability = Counter(r["ai_preliminary_educational_suitability"] for r in matrix)
    comparison = Counter(r["ai_preliminary_comparison_to_a001"] for r in matrix)
    query_quality = Counter(r["ai_preliminary_query_correctness"] for r in matrix)
    manifest["status"] = "IMAGE_ATTEMPTS_COMPLETE_OWNER_REVIEW_PENDING"
    manifest["completed_image_ids"] = list(retrieval)
    manifest["blockers"] = [{"stage": "query", "ids": [x["vocab_id"] for x in blocked],
                              "reason": "Invalid Qwen output or missing approved semantic intent; no image search attempted"}]
    write_json(HERE / "experiment_manifest.json", manifest)
    report = f'''# A-004 complete attempt report — 2026-11-23

**All 100 vocabulary IDs have final processing states; {search_attempts}/100 had real image-search attempts.** The seven query-blocked IDs were not searched. This completes the eligible image benchmark attempts, not human image approval or a claim that every ID succeeded.

## Frozen run and actual outcomes

- Dataset SHA-256 `{manifest["dataset_sha256"]}`; 100 unique IDs; original Qwen output retained, with {qcounts["SUCCESS"]} effective queries, {qcounts["FAILED"]} invalid outputs and {qcounts["BLOCKED_SEMANTIC_DECISION"]} missing approved image intent. No Qwen rerun.
- Image searches: {search_attempts}/100 attempted, {search_successes} search calls succeeded. {icounts["RANKED"]} IDs ranked once by the frozen SigLIP model; {icounts["NO_VALID_CANDIDATES"]} had no valid download; {icounts["FAILED"]} other processing failures; {icounts["SKIPPED_QUERY"]} blocked before search. The only first-batch unranked item, vocab-000008, had one HTTP 404 candidate URL; the old failure was preserved and not retried.
- Candidates: {len(candidates)} records, {downloads["SUCCESS"]} valid downloads with matching raw/JPEG hashes, {downloads["FAILED"]} failed downloads. No old success was redownloaded and no prior SigLIP ranking was repeated. Ten 10-ID image batches are recorded in the manifest.
- Existing A-001 audio references: {audio["hash_match"]}/100 hash-match, no regeneration. Canonical vocabulary, production media and owner-approved image manifests were not changed.

## AI_PRELIMINARY evaluation

- New top-1 image semantic relevance: {dict(relevance)}. Educational suitability: {dict(suitability)}. Compared with A-001 images: {dict(comparison)}. `NOT_ASSESSED` and `NOT_COMPARABLE` are excluded from any quality-rate denominator. All image judgments remain unverified by the owner.
- The query validator accepted 94 normalized outputs; 93 have an effective image intent. Desk review of all frozen effective query strings against English/Vietnamese vocabulary gives AI_PRELIMINARY query correctness {dict(query_quality)}. Obvious mismatches include `rain illumination`, `today timepiece`, `yesterday place`, `family institution`, `write action` and `hello object`. Seven blocked IDs and exact reasons are in [query remediation](query_remediation.json). Query syntax is not proof of semantic correctness.
- Candidate ranks are SigLIP scores, not human judgments. Review text, composition, watermarks, retrieval gaps and lower-ranked alternatives in the [internal gallery](review_gallery.html). `NO_SUITABLE_IMAGE` is an explicit owner-review choice; no new outcome is auto-approved.

## Evidence and next review

[Manifest](experiment_manifest.json), [query ledger](query_results.json), [retrieval ledger](retrieval_results.json), [candidate table](candidate_rankings.csv), [100-ID matrix](evaluation_matrix.csv) and the gallery retain status, source URLs, hashes, ranks and failures. Reviewer should inspect all 100 cards, choose an image or `NO_SUITABLE_IMAGE` where appropriate, add notes and export JSON. No public-rights approval or production promotion follows automatically. B-003.2 and Game UX/UI remain outside this task.
'''
    (HERE / "evaluation_report.md").write_text(report, encoding="utf-8")
    print("queries", dict(qcounts), "images", dict(icounts), "search", search_attempts, search_successes,
          "candidates", len(candidates), dict(downloads), "quality", dict(suitability))


if __name__ == "__main__":
    main()
