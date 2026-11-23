"""Offline re-check of the transparency fix on already-downloaded raw candidates (no network, no Qwen).

For every A-003 arm and A002_ICON_PILOT_20 item that has at least one transparent raw candidate:
re-normalize ALL its raws with the fixed `normalize_image_to_jpeg` into this folder, re-score them
with the fixed `score_batch` against the same query text, and compare selection before/after.
Original experiment files are read-only.
"""

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "collect data script"))
from image_scorer import SiglipImageScorer  # noqa: E402
from imagecollector import normalize_image_to_jpeg  # noqa: E402

A003 = ROOT / "reports/image_pipeline_experiments/A003_CONDITIONAL_SEARCH/retrieval_results.json"
PILOT = ROOT / "reports/image_pipeline_experiments/A002_ICON_PILOT_20/retrieval_results.json"


def has_alpha(path):
    with Image.open(path) as image:
        return "A" in image.mode or "transparency" in image.info


def mean_luma(path):
    with Image.open(path) as image:
        return ImageStat.Stat(image.convert("L")).mean[0]


def groups():
    for p in json.loads(A003.read_text(encoding="utf-8"))["pairs"]:
        yield "A003", f"{p['vocab_id']}/{p['arm']}", p["query"], p["selected_candidate_id"], p["candidates"], "query_score"
    for p in json.loads(PILOT.read_text(encoding="utf-8"))["items"]:
        yield "PILOT20", f"{p['vocab_id']}/ICON", p["query"], p["selected_candidate_id"], p["candidates"], "siglip_score"


def main():
    before = {name: hashlib.sha256(name.read_bytes()).hexdigest() for name in (A003, PILOT)}
    scorer = SiglipImageScorer()
    out = []
    for source, key, query, old_selected, candidates, score_field in groups():
        valid = [c for c in candidates if c["status"] == "DOWNLOADED" and c.get("raw_path")]
        if not any(has_alpha(ROOT / c["raw_path"]) for c in valid):
            continue
        folder = HERE / "images" / source / key
        folder.mkdir(parents=True, exist_ok=True)
        rows = []
        for c in valid:
            raw = ROOT / c["raw_path"]
            fixed = folder / (c["candidate_id"].split("-")[-1] + ".jpg")
            normalize_image_to_jpeg(raw, fixed)
            rows.append({"candidate_id": c["candidate_id"], "alpha": has_alpha(raw),
                         "old_jpg": c["image_path"], "old_mean_luma": round(mean_luma(ROOT / c["image_path"]), 1),
                         "new_jpg": fixed.relative_to(ROOT).as_posix(), "new_mean_luma": round(mean_luma(fixed), 1),
                         "new_sha256": hashlib.sha256(fixed.read_bytes()).hexdigest(),
                         "old_score": c.get(score_field)})
        scores = scorer.score_batch(query, [ROOT / c["raw_path"] for c in valid])
        for row, score in zip(rows, scores, strict=True):
            row["new_score"] = score.score
        new_selected = max(rows, key=lambda r: r["new_score"])["candidate_id"]
        out.append({"source": source, "key": key, "query": query, "old_selected": old_selected,
                    "new_selected": new_selected, "selection_changed": new_selected != old_selected,
                    "old_selected_was_alpha": any(r["alpha"] for r in rows if r["candidate_id"] == old_selected),
                    "black_before": sum(r["alpha"] and r["old_mean_luma"] < 12 for r in rows),
                    "black_after": sum(r["new_mean_luma"] < 12 for r in rows), "candidates": rows})
        print(source, key, old_selected[-6:], "->", new_selected[-6:], flush=True)
    after = {name: hashlib.sha256(name.read_bytes()).hexdigest() for name in (A003, PILOT)}
    assert before == after, "source results changed"
    summary = {src: {"groups": sum(g["source"] == src for g in out),
                     "selection_changed": [g["key"] for g in out if g["source"] == src and g["selection_changed"]],
                     "black_before": sum(g["black_before"] for g in out if g["source"] == src),
                     "black_after": sum(g["black_after"] for g in out if g["source"] == src)} for src in ("A003", "PILOT20")}
    (HERE / "recheck_results.json").write_text(json.dumps({"summary": summary, "groups": out}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
