"""Offline A-003 diagnostic: score existing raw candidates with frozen meaning text."""
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "collect data script"))
from image_scorer import SiglipImageScorer  # noqa: E402

SOURCE = ROOT / "reports/image_pipeline_experiments/A003_CONDITIONAL_SEARCH/retrieval_results.json"
feedback = json.loads((HERE / "owner_feedback.json").read_text(encoding="utf-8"))
descriptions = feedback["semantic_descriptions_frozen_before_scoring"]
pairs = [p for p in json.loads(SOURCE.read_text(encoding="utf-8"))["pairs"] if p["vocab_id"] in descriptions]
assert len(pairs) == 14
scorer = SiglipImageScorer()
rows = []
for pair in pairs:
    valid = [c for c in pair["candidates"] if c["status"] == "DOWNLOADED"]
    paths = [ROOT / c["raw_path"] for c in valid]
    assert all(hashlib.sha256(p.read_bytes()).hexdigest() == c["raw_sha256"] for p, c in zip(paths, valid))
    query_scores = [s.score for s in scorer.score_batch(pair["query"], paths)]
    meaning_scores = [s.score for s in scorer.score_batch(descriptions[pair["vocab_id"]], paths)]
    original_order = sorted(valid, key=lambda c: c["query_score"], reverse=True)
    query_order = sorted(range(len(valid)), key=lambda i: query_scores[i], reverse=True)
    meaning_order = sorted(range(len(valid)), key=lambda i: meaning_scores[i], reverse=True)
    for i, candidate in enumerate(valid):
        rows.append({
            "vocab_id": pair["vocab_id"], "arm": pair["arm"], "candidate_id": candidate["candidate_id"],
            "retrieval_rank": candidate["retrieval_rank"], "raw_path": candidate["raw_path"],
            "raw_sha256": candidate["raw_sha256"], "original_query": pair["query"],
            "meaning_text": descriptions[pair["vocab_id"]], "original_query_score": candidate["query_score"],
            "original_query_rank": original_order.index(candidate) + 1,
            "post_fix_query_score": query_scores[i], "post_fix_query_rank": query_order.index(i) + 1,
            "post_fix_meaning_score": meaning_scores[i], "post_fix_meaning_rank_arm": meaning_order.index(i) + 1,
            "original_selected": candidate["candidate_id"] == pair["selected_candidate_id"],
        })
    print(pair["vocab_id"], pair["arm"], "done", flush=True)

for vocab_id in descriptions:
    group = [r for r in rows if r["vocab_id"] == vocab_id]
    order = sorted(group, key=lambda r: r["post_fix_meaning_score"], reverse=True)
    for row in group:
        row["post_fix_meaning_rank_pooled"] = order.index(row) + 1

with (HERE / "scoring_comparison.csv").open("w", encoding="utf-8-sig", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
