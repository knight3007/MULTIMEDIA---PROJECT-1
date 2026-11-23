"""Record desk visual observations of every A-003.1 candidate; no assets changed."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "reports/image_pipeline_experiments/A003_CONDITIONAL_SEARCH/retrieval_results.json"
PAIRS = json.loads(SOURCE.read_text(encoding="utf-8"))["pairs"]
IDS = set(json.loads((HERE / "owner_feedback.json").read_text(encoding="utf-8"))["semantic_descriptions_frozen_before_scoring"])

# Suitable means visually useful for the vocabulary meaning, not rights-cleared or owner-approved.
SUITABLE = {
    "vocab-000021": {"NORMAL": {5}, "ICON": {1, 2, 4, 5, 6}},
    "vocab-000031": {"NORMAL": set(), "ICON": {1, 2, 3, 6}},
    "vocab-000057": {"NORMAL": {2, 3, 4, 5, 6, 7}, "ICON": set()},
    "vocab-000059": {"NORMAL": set(), "ICON": {1, 2, 5}},
    "vocab-000063": {"NORMAL": set(), "ICON": {1, 2, 4, 5, 6, 7}},
    "vocab-000046": {"NORMAL": {5}, "ICON": {1, 2, 4, 5, 6, 7}},
    "vocab-000083": {"NORMAL": set(), "ICON": set()},
}
NOTES = {
    "vocab-000021-NORMAL-01": "Unfinished timber frame; not a completed house",
    "vocab-000021-NORMAL-05": "Complete constructed house photograph",
    "vocab-000021-ICON-03": "Pre-fix JPEG flattened to black square; raw transparency composited by FIX-001",
    "vocab-000031-NORMAL-06": "Book-object-art exhibition poster; wrong referent and prominent text",
    "vocab-000031-ICON-04": "Sheet of multiple book symbols; cluttered",
    "vocab-000031-ICON-03": "Single open-book illustration",
    "vocab-000057-ICON-07": "Music artist portrait; name collision in retrieval",
    "vocab-000059-NORMAL-01": "Action retail storefront; wrong meaning",
    "vocab-000059-ICON-06": "BUY text button; answer leakage",
    "vocab-000063-ICON-03": "Receive Icons web-page screenshot; several tiny icons and printed text",
    "vocab-000063-ICON-02": "Large hand-and-parcel graphic intrinsic to asset; meaning is clear",
    "vocab-000046-NORMAL-01": "Hunger versus appetite infographic; text dominates",
    "vocab-000046-ICON-01": "Food thought pictogram; clear hungry state",
    "vocab-000046-ICON-03": "Low contrast subject on dark background in historical JPEG",
    "vocab-000083-NORMAL-04": "Event poster using Sometimes as a name, not frequency",
    "vocab-000083-ICON-01": "Unrelated visual-search web-page screenshot",
}
DEFAULT_ISSUE = {
    "vocab-000021": {"NORMAL": "Construction/query drift or chart", "ICON": "Simplified house pictogram"},
    "vocab-000031": {"NORMAL": "Book collage, poster, watermark or sculpture", "ICON": "Book illustration"},
    "vocab-000057": {"NORMAL": "Person eating food", "ICON": "Music artist/name collision"},
    "vocab-000059": {"NORMAL": "Action store or action figures", "ICON": "Shopping/cart icon or printed BUY"},
    "vocab-000063": {"NORMAL": "Text-heavy worksheet or unrelated software", "ICON": "Receiving-parcel icon or web screenshot"},
    "vocab-000046": {"NORMAL": "Hunger/appetite text infographic", "ICON": "Hungry/food pictogram"},
    "vocab-000083": {"NORMAL": "Event, grammar text or book title", "ICON": "Unrelated visual-search screenshot"},
}
rows = []
for pair in PAIRS:
    if pair["vocab_id"] not in IDS:
        continue
    for c in pair["candidates"]:
        if c["status"] == "DOWNLOADED":
            for kind in ("raw", "image"):
                path = ROOT / c[f"{kind}_path"]
                assert hashlib.sha256(path.read_bytes()).hexdigest() == c[f"{kind}_sha256"]
        suitable = c["retrieval_rank"] in SUITABLE[pair["vocab_id"]][pair["arm"]]
        rows.append({
            "vocab_id": pair["vocab_id"], "arm": pair["arm"], "candidate_id": c["candidate_id"],
            "retrieval_rank": c["retrieval_rank"], "download_status": c["status"],
            "original_selected": c["candidate_id"] == pair["selected_candidate_id"],
            "original_query_score": c["query_score"], "raw_path": c["raw_path"], "raw_sha256": c["raw_sha256"],
            "gallery_image_path": c["image_path"], "gallery_image_sha256": c["image_sha256"],
            "source_url": c["source_url"], "analyst_visual_judgement": "SUITABLE" if suitable else "UNSUITABLE" if c["status"] == "DOWNLOADED" else "UNAVAILABLE",
            "visual_note": NOTES.get(c["candidate_id"], DEFAULT_ISSUE[pair["vocab_id"]][pair["arm"]]),
        })
with (HERE / "candidate_diagnosis.csv").open("w", encoding="utf-8-sig", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(len(rows), "candidate records verified")
