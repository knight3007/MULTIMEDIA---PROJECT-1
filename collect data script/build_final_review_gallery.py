"""Build the final private HTML review gallery from a validated Content Pack.

Run from the repository root:
python "collect data script/build_final_review_gallery.py" "reports/EXCEL_FULL_PIPELINE_FINAL/run-88c4196d-dc59-497e-a389-76a564615483"
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from content_pack_builder import validate_pack

PACK_NAME = "content_pack_v301"
HERE = Path(__file__).resolve().parent


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def embed_json(value) -> str:
    """Keep imported text inert inside an inline script while retaining Unicode."""
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            .replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def load_review_data(run_dir: Path, pack_name: str = PACK_NAME):
    run_dir = Path(run_dir).resolve()
    pack_dir = run_dir / pack_name
    pack_path = pack_dir / "content_pack.json"
    pack = read_json(pack_path)
    validation = validate_pack(pack, pack_dir)
    if not validation["valid"]:
        raise ValueError("Content Pack validation failed: " + "; ".join(validation["errors"][:5]))
    image_results = {entry["item_id"]: entry for entry in read_json(run_dir / "image_selection_manifest.json")}
    audio_results = read_json(run_dir / "audio_manifest.json")
    cards, seen = [], set()
    for item in pack["items"]:
        item_id = item["item_id"]
        if item_id in seen:
            raise ValueError(f"Duplicate item ID: {item_id}")
        seen.add(item_id)
        image_result = image_results[item_id]
        audio_result = audio_results[item_id]
        image_asset = item["image"]
        if image_asset and image_result.get("image_sha256") != image_asset["sha256"]:
            raise ValueError(f"Image selection hash mismatch: {item_id}")
        if not image_asset and image_result.get("status") not in {"NO_SUITABLE_IMAGE", "NEEDS_CURATION", "SEARCH_FAILED", "QUERY_FAILED", "SCORING_FAILED", "IMAGE_FAILED", "PROPOSED"}:
            raise ValueError(f"Missing image needs explicit outcome: {item_id}")
        audios = {}
        for locale, text_key, asset_key in (("en", "english", "audio_english"), ("ja", "japanese", "audio_japanese")):
            asset = item.get(asset_key)
            result = audio_result[locale]
            if (result.get("item_id") != item_id or result.get("locale") != locale
                    or result.get("text") != item[text_key]
                    or bool(asset) != (result.get("status") in {"GENERATED", "REUSED"})
                    or asset and asset["sha256"] != result.get("sha256")):
                raise ValueError(f"Audio association mismatch: {item_id}/{locale}")
            audios[locale] = ({"path": f"{pack_name}/{asset['path']}", "sha256": asset["sha256"],
                               "text": item[text_key], "locale": locale, "status": result["status"],
                               "duration": result["duration_seconds"], "provider": result["provider"]}
                              if asset else None)
        image = ({"path": f"{pack_name}/{image_asset['path']}", "sha256": image_asset["sha256"],
                  "strategy": image_result.get("query_strategy") or image_result.get("route"),
                  "source": image_result.get("owner_decision_source") or image_result.get("query"),
                  "restriction": image_result.get("usage_restriction")}
                 if image_asset else None)
        warnings = [error["code"] for error in item["errors"]]
        if item["distribution"]["status"] == "restricted":
            warnings.append("INTERNAL_ONLY")
        if item.get("target_sense"):
            warnings.append("TARGET_SENSE_REVIEW")
        cards.append({"id": item_id, "row": item["source_row"], "english": item["english"],
                      "japanese": item["japanese"], "vietnamese": item["vietnamese"],
                      "target_sense": item["target_sense"], "status": item["status"],
                      "review_status": item["review_status"], "technical": item["technical_integrity"],
                      "image_status": image_result["status"], "image": image,
                      "audio_en": audios["en"], "audio_ja": audios["ja"], "warnings": warnings})
    if set(image_results) != seen or set(audio_results) != seen:
        raise ValueError("Manifest and Content Pack item IDs differ")
    summary = {"items": len(cards), "images": sum(bool(c["image"]) for c in cards),
               "missing_images": sum(not c["image"] for c in cards),
               "english_audio": sum(bool(c["audio_en"]) for c in cards),
               "japanese_audio": sum(bool(c["audio_ja"]) for c in cards),
               "needs_review": sum(c["status"] == "needs_review" for c in cards),
               "errors": sum(bool(c["warnings"]) and c["status"] == "failed" for c in cards)}
    return cards, summary


def build(run_dir: Path, pack_name: str = PACK_NAME):
    run_dir = Path(run_dir).resolve()
    target = run_dir / "final_review_gallery.html"
    report_path = run_dir / "final_gallery_validation_report.json"
    if target.exists() or report_path.exists():
        raise FileExistsError("Final gallery or validation report already exists; preserve previous output")
    cards, summary = load_review_data(run_dir, pack_name)
    template = (HERE / "final_review_gallery_template.html").read_text(encoding="utf-8")
    page = template.replace("__CARDS_JSON__", embed_json(cards)).replace("__SUMMARY_JSON__", embed_json(summary))
    if "__CARDS_JSON__" in page or "__SUMMARY_JSON__" in page or "D:\\" in page:
        raise ValueError("Gallery template did not render safely")
    target.write_text(page, encoding="utf-8", newline="\n")
    pack_path = run_dir / pack_name / "content_pack.json"
    report = {"valid": True, "source_content_pack": f"{pack_name}/content_pack.json",
              "source_sha256": hashlib.sha256(pack_path.read_bytes()).hexdigest(),
              "summary": summary, "missing_media": [{"id": c["id"], "english": c["english"],
                            "image": c["image"] is None, "english_audio": c["audio_en"] is None,
                            "japanese_audio": c["audio_ja"] is None} for c in cards
                            if not c["image"] or not c["audio_en"] or not c["audio_ja"]],
              "restricted_items": [c["id"] for c in cards if "INTERNAL_ONLY" in c["warnings"]],
              "browser_verification": "pending"}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--pack-name", default=PACK_NAME)
    args = parser.parse_args()
    print(json.dumps(build(args.run_dir, args.pack_name), ensure_ascii=False))
