"""Freeze expected word-type routes from the owner-approved A004R final selection BEFORE running prompt v2.

PHOTO: concrete nouns the owner accepted from Qwen's default query -> v2 must keep them CONCRETE.
NON_PHOTO: words that only worked with icon/scene queries -> v2 must route them away from CONCRETE.
CURATE: connector word -> v2 must return CONNECTOR.
ANY: ambiguous (abstract nouns or adjectives accepted with default queries, concrete nouns accepted as icons).
"""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MANIFEST = ROOT / "reports/image_pipeline_experiments/A004R_FINAL_SELECTION/final_selection_manifest.json"
ANY = {"sun", "family", "friend", "book", "computer", "dictionary", "happy", "beautiful", "eat", "drink", "different",
       "sorry", "problem", "sometimes", "database", "password", "music", "weather", "winter", "software"}


def main():
    out = HERE / "expected_routes.csv"
    if out.exists():
        raise SystemExit("expected_routes.csv already frozen; refusing to overwrite")
    items = json.loads(MANIFEST.read_text(encoding="utf-8"))["items"]
    rows = []
    for item in items:
        word, strategy = item["english"], item["query_strategy"]
        if word in ANY:
            expected = "ANY"
        elif strategy == "CURATED_CONCEPT":
            expected = "CURATE"
        elif strategy.startswith("QWEN_DEFAULT"):
            expected = "PHOTO"
        else:
            expected = "NON_PHOTO"
        rows.append({"vocab_id": item["vocab_id"], "english": word, "approved_strategy": strategy,
                     "approved_query": item["search_query"], "expected_route": expected})
    with out.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    counts = {k: sum(r["expected_route"] == k for r in rows) for k in ("PHOTO", "NON_PHOTO", "CURATE", "ANY")}
    (HERE / "acceptance_criteria.json").write_text(json.dumps({
        "expected_routes_sha256": digest, "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "counts": counts,
        "criteria": {"PHOTO_kept_concrete_min": 0.90, "NON_PHOTO_routed_away_min": 0.85,
                     "CURATE_exact": True, "valid_query_after_one_retry": 1.0},
        "max_prompt_iterations": 3,
        "note": "Frozen before any prompt v2 inference. Prompt examples must not use benchmark words."},
        indent=2) + "\n", encoding="utf-8")
    print(counts, digest[:12])


if __name__ == "__main__":
    main()
