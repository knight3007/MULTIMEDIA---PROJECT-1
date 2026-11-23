"""Validate the owner-supplied A-003.2 export and write an internal selection manifest."""
import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REPAIR = ROOT / "reports/image_pipeline_experiments/A003_SELECTIVE_REPAIR"
A003 = ROOT / "reports/image_pipeline_experiments/A003_CONDITIONAL_SEARCH"
DIAG = ROOT / "reports/image_pipeline_experiments/A003_RANKING_DIAGNOSIS"
SOURCE = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else HERE / "owner_review_export.json"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local_asset(path, expected):
    target = (ROOT / path).resolve()
    assert target.is_relative_to(ROOT) and target.is_file(), path
    assert digest(target) == expected, path
    return target


review_bytes = SOURCE.read_bytes()
review = json.loads(review_bytes)
assert review["task_id"] == "A-003.2"
assert review["kind"] == "HUMAN_REVIEW_DRAFT_NOT_AUTO_APPROVAL"
assert isinstance(review["reviewer"], str) and review["reviewer"].strip()
assert datetime.fromisoformat(review["exported_at"].replace("Z", "+00:00")).tzinfo
rows = list(csv.DictReader((REPAIR / "proposed_image_selections.csv").open(encoding="utf-8-sig", newline="")))
proposal_by_id = {row["vocab_id"]: row for row in rows}
assert len(rows) == len(proposal_by_id) == 7
feedback = json.loads((DIAG / "owner_feedback.json").read_text(encoding="utf-8"))
assert set(proposal_by_id) == {item["vocab_id"] for item in feedback["feedback"]}
vocab = {r["vocab_id"]: r for r in json.loads((ROOT / "data/vocabulary/unified_dataset_v1.json").read_text(encoding="utf-8"))["records"]}
assert set(review["reviews"]) == set(proposal_by_id)
assert len(review["proposals"]) == 7
assert {p["vocab_id"] for p in review["proposals"]} == set(proposal_by_id)
for proposed in review["proposals"]:
    row = proposal_by_id[proposed["vocab_id"]]
    assert proposed == {"vocab_id": row["vocab_id"], "proposed_candidate_id": row["proposed_candidate_id"],
                        "proposed_sha256": row["proposed_sha256"], "proposed_outcome": row["proposed_outcome"]}

original = json.loads((A003 / "retrieval_results.json").read_text(encoding="utf-8"))["pairs"]
targeted = json.loads((REPAIR / "targeted_retrieval_results.json").read_text(encoding="utf-8"))["variants"]
candidates = {}
for source, groups in (("A003_CONDITIONAL_SEARCH", original), ("A003_SELECTIVE_REPAIR", targeted)):
    for group in groups:
        for c in group["candidates"]:
            cid = c["candidate_id"]
            assert cid not in candidates
            candidates[cid] = (source, c)

approved = []
no_image = []
unresolved = []
for vid, row in proposal_by_id.items():
    record = vocab[vid]
    assert (record["english"], record["japanese"]["display"], record["vietnamese"]) == (row["english"], row["japanese"], row["vietnamese"])
    local_asset(row["a001_baseline_path"], row["a001_baseline_sha256"])
    local_asset(row["comparison_current_path"], row["comparison_current_sha256"])
    action = review["reviews"][vid]
    assert set(action) == {"decision", "notes"} and isinstance(action["notes"], str)
    decision = action["decision"]
    assert decision in {"ACCEPT_PROPOSED", "KEEP_ORIGINAL", "NONE_SUITABLE", "NEEDS_REVIEW"}
    common = {"vocab_id": vid, "english": row["english"], "japanese": row["japanese"],
              "vietnamese": row["vietnamese"], "review_decision": decision, "review_notes": action["notes"]}
    if decision == "ACCEPT_PROPOSED":
        assert row["proposed_outcome"] == "CANDIDATE_FOR_REVIEW" and row["proposed_candidate_id"]
        cid = row["proposed_candidate_id"]
        source, c = candidates[cid]
        assert cid.startswith(vid + "-") and c["status"] == "DOWNLOADED"
        assert (c["image_path"], c["image_sha256"], c["source_url"]) == (row["proposed_path"], row["proposed_sha256"], row["proposed_source_url"])
        local_asset(c["image_path"], c["image_sha256"])
        local_asset(c["raw_path"], c["raw_sha256"])
        approved.append({**common, "candidate_id": cid, "image_path": c["image_path"],
                         "image_sha256": c["image_sha256"], "raw_sha256": c["raw_sha256"],
                         "source_url": c["source_url"], "source_experiment": source,
                         "quality_decision": "OWNER_ACCEPTED", "public_eligibility": "UNKNOWN_RIGHTS_NOT_CLEARED",
                         "production_status": "NOT_PROMOTED"})
    elif decision == "NONE_SUITABLE":
        assert row["proposed_outcome"] == "NO_SUITABLE_IMAGE" and not row["proposed_candidate_id"]
        no_image.append({**common, "outcome": "NO_SUITABLE_IMAGE", "production_status": "NOT_APPLIED"})
    elif decision == "KEEP_ORIGINAL":
        local_asset(row["comparison_current_path"], row["comparison_current_sha256"])
        unresolved.append({**common, "reason": "KEEP_ORIGINAL requires an explicit selection interpretation before promotion"})
    else:
        unresolved.append({**common, "reason": "Owner requested further review"})

# Only explicit owner feedback rejects an individual candidate. Other images are not individually rated.
explicit_rejections = {
    "vocab-000083-NORMAL-04": "Owner: both original and icon images unsuitable",
    "vocab-000083-ICON-01": "Owner: both original and icon images unsuitable",
    "vocab-000031-NORMAL-06": "Owner: original image unsuitable",
    "vocab-000021-NORMAL-01": "Owner requires a complete constructed house; this selected image is an unfinished frame",
}
assert set(explicit_rejections).isdisjoint({item["candidate_id"] for item in approved})
dispositions = []
reviewed_ids = set(proposal_by_id)
for cid, (source, c) in candidates.items():
    vid = cid[:12]
    if vid not in reviewed_ids:
        continue
    if c["status"] == "DOWNLOADED":
        local_asset(c["image_path"], c["image_sha256"])
        local_asset(c["raw_path"], c["raw_sha256"])
    status = ("OWNER_ACCEPTED" if cid in {item["candidate_id"] for item in approved}
              else "OWNER_REJECTED_EXPLICIT" if cid in explicit_rejections
              else "UNAVAILABLE_DOWNLOAD_FAILED" if c["status"] != "DOWNLOADED"
              else "NOT_INDIVIDUALLY_REVIEWED")
    dispositions.append({"vocab_id": vid, "candidate_id": cid, "source_experiment": source,
                         "download_status": c["status"], "owner_disposition": status,
                         "reason": explicit_rejections.get(cid, ""), "image_path": c.get("image_path") or "",
                         "image_sha256": c.get("image_sha256") or "", "source_url": c.get("source_url") or ""})
assert len(dispositions) == 103
assert len(approved) + len(no_image) + len(unresolved) == 7
override = json.loads((ROOT / "data/vocabulary/internal_image_overrides_v1.json").read_text(encoding="utf-8"))["overrides"]
because = next(x for x in override if x["vocab_id"] == "vocab-000081")
assert because["usage_restriction"] == "INTERNAL_ONLY_TEMPORARY" and because["public_use"] == "NOT_ALLOWED_UNTIL_RIGHTS_CLEARED_OR_REPLACED"

manifest = {
    "task_id": "A-003.3", "status": "SEVEN_ITEM_OWNER_REVIEW_CONSOLIDATED",
    "source_export": {"original_path": SOURCE.as_posix(), "copied_path": "reports/image_pipeline_experiments/A003_OWNER_DECISIONS/owner_review_export.json",
                      "sha256": hashlib.sha256(review_bytes).hexdigest(), "reviewer": review["reviewer"],
                      "exported_at": review["exported_at"], "kind": review["kind"]},
    "consolidated_at_utc": datetime.now(timezone.utc).isoformat(),
    "reviewed_item_count": 7, "approved_image_count": len(approved),
    "no_suitable_image_count": len(no_image), "unresolved_item_count": len(unresolved),
    "approved_image_selections": approved, "no_suitable_image_outcomes": no_image,
    "unresolved_items": unresolved,
    "candidate_disposition_file": "reports/image_pipeline_experiments/A003_OWNER_DECISIONS/candidate_disposition.csv",
    "candidate_disposition_counts": dict(Counter(x["owner_disposition"] for x in dispositions)),
    "prior_evidence": {"ai_preliminary": "reports/image_pipeline_experiments/A003_CONDITIONAL_SEARCH/evaluation_report.md",
                       "owner_chat_feedback": "reports/image_pipeline_experiments/A003_RANKING_DIAGNOSIS/owner_feedback.json",
                       "repair_proposals": "reports/image_pipeline_experiments/A003_SELECTIVE_REPAIR/proposed_image_selections.csv"},
    "because_restriction_unchanged": {"vocab_id": because["vocab_id"], "candidate_id": because["selection"]["candidate_id"],
                                      "usage_restriction": because["usage_restriction"], "public_use": because["public_use"]},
    "scope_limit": "Quality decisions for seven A-003.2 items only; no production promotion or public rights clearance"
}
HERE.mkdir(parents=True, exist_ok=True)
(HERE / "owner_review_export.json").write_bytes(review_bytes)
(HERE / "final_image_selection_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
with (HERE / "candidate_disposition.csv").open("w", encoding="utf-8-sig", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=list(dispositions[0]))
    writer.writeheader()
    writer.writerows(dispositions)
print("approved", len(approved), "no_image", len(no_image), "unresolved", len(unresolved),
      "candidate_dispositions", dict(Counter(x["owner_disposition"] for x in dispositions)))
